import csv
import json
import os
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from apps.publications.models import Publication
from apps.researchers.models import Researcher


SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
SERIAL_TITLE_URL = "https://api.elsevier.com/content/serial/title"
ABSTRACT_EID_URL = "https://api.elsevier.com/content/abstract/eid"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_PAPER_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
MAX_SYNC_COUNT = 20


class Command(BaseCommand):
    help = "Sync publication metadata from Scopus into the Publication model."

    def add_arguments(self, parser):
        parser.add_argument("--query", help="Scopus query, e.g. AU-ID(7004212771)")
        parser.add_argument(
            "--author-name",
            help='Researcher name, e.g. "John Smith" or "J Smith". The command will build a Scopus author query for you.',
        )
        parser.add_argument(
            "--from-site-researchers",
            action="store_true",
            help="Use researchers stored in the website database as the sync source.",
        )
        parser.add_argument(
            "--researcher-id",
            type=int,
            help="Sync one researcher from the website database by Researcher.id.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help=f"Number of results to request (max {MAX_SYNC_COUNT})",
        )
        parser.add_argument("--start", type=int, default=0, help="Offset for Scopus search results")
        parser.add_argument("--api-key", help="Elsevier API key. Defaults to SCOPUS_API_KEY env var")
        parser.add_argument(
            "--view",
            default="STANDARD",
            choices=["STANDARD", "COMPLETE"],
            help="Scopus Search API view. STANDARD is safer for keys with limited entitlements.",
        )
        parser.add_argument(
            "--impact-factor-csv",
            help="Optional CSV file with journal impact factor data to merge after Scopus sync",
        )

    def handle(self, *args, **options):
        api_key = options.get("api_key") or os.environ.get("SCOPUS_API_KEY")
        if not api_key:
            raise CommandError("Provide --api-key or set SCOPUS_API_KEY in your environment.")

        count = clamp_count(options["count"])
        start = options["start"]
        view = options["view"]
        impact_factor_rows = load_impact_factor_csv(options.get("impact_factor_csv"))
        sync_target = resolve_sync_target(
            raw_query=options.get("query"),
            author_name=options.get("author_name"),
            from_site_researchers=options.get("from_site_researchers"),
            researcher_id=options.get("researcher_id"),
        )

        if sync_target["mode"] == "single_query":
            created_count, updated_count, processed_count = sync_query_into_publications(
                api_key=api_key,
                query=sync_target["query"],
                count=count,
                start=start,
                view=view,
                impact_factor_rows=impact_factor_rows,
                stdout=self.stdout,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Scopus sync completed. Created {created_count}, updated {updated_count}, total processed {processed_count}."
                )
            )
            return

        researchers = sync_target["researchers"]
        total_created = 0
        total_updated = 0
        total_processed = 0

        for researcher in researchers:
            researcher_query = build_query_from_researcher(researcher)
            self.stdout.write("")
            self.stdout.write(f"Syncing researcher: {researcher.full_name}")
            self.stdout.write(f"Using Scopus query: {researcher_query}")
            created_count, updated_count, processed_count = sync_query_into_publications(
                api_key=api_key,
                query=researcher_query,
                count=count,
                start=start,
                view=view,
                impact_factor_rows=impact_factor_rows,
                stdout=self.stdout,
            )
            total_created += created_count
            total_updated += updated_count
            total_processed += processed_count

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Scopus sync completed for {len(researchers)} researcher(s). "
                f"Created {total_created}, updated {total_updated}, total processed {total_processed}."
            )
        )


def search_scopus(api_key, query, count, start, view, stdout):
    params = {
        "query": query,
        "count": count,
        "start": start,
        "view": view,
    }

    try:
        return call_json_api(SEARCH_URL, api_key, params)
    except CommandError as exc:
        message = str(exc)
        if view == "COMPLETE" and "AUTHORIZATION_ERROR" in message:
            stdout.write(
                "COMPLETE view is not available for this API key. Falling back to STANDARD view."
            )
            params["view"] = "STANDARD"
            return call_json_api(SEARCH_URL, api_key, params)
        raise


def resolve_sync_target(raw_query, author_name, from_site_researchers, researcher_id):
    option_count = sum(
        bool(value)
        for value in [raw_query, author_name, from_site_researchers, researcher_id]
    )
    if option_count != 1:
        raise CommandError(
            "Choose exactly one sync source: --query, --author-name, --from-site-researchers, or --researcher-id."
        )

    if from_site_researchers:
        researchers = list(Researcher.objects.filter(is_active=True))
        if not researchers:
            raise CommandError("No active researchers found in the website database.")
        return {"mode": "site_researchers", "researchers": researchers}

    if researcher_id:
        try:
            researcher = Researcher.objects.get(pk=researcher_id)
        except Researcher.DoesNotExist as exc:
            raise CommandError(f"Researcher with id {researcher_id} was not found.") from exc
        return {"mode": "site_researchers", "researchers": [researcher]}

    return {"mode": "single_query", "query": resolve_query(raw_query, author_name)}


def clamp_count(value):
    if value < 1:
        raise CommandError("Count must be at least 1.")
    if value > MAX_SYNC_COUNT:
        return MAX_SYNC_COUNT
    return value


def resolve_query(raw_query, author_name):
    if raw_query:
        return raw_query
    if author_name:
        return build_author_query(author_name)
    raise CommandError("Provide --query or --author-name.")


def build_query_from_researcher(researcher):
    if researcher.scopus_author_id:
        author_id = escape_scopus_value(researcher.scopus_author_id)
        return f"AU-ID({author_id})"
    return build_author_query(researcher.full_name)


def sync_query_into_publications(api_key, query, count, start, view, impact_factor_rows, stdout):
    stdout.write(f"Using Scopus query: {query}")
    payload = search_scopus(api_key, query=query, count=count, start=start, view=view, stdout=stdout)

    entries = payload.get("search-results", {}).get("entry", [])
    if not entries:
        stdout.write("No Scopus results were returned for this query.")
        return 0, 0, 0

    metric_cache = {}
    created_count = 0
    updated_count = 0

    for entry in entries:
        metrics = {}
        issn = clean_issn(entry.get("prism:issn", ""))
        source_id = stringify(entry.get("source-id"))
        if issn or source_id:
            cache_key = f"{issn}|{source_id}"
            if cache_key not in metric_cache:
                metric_cache[cache_key] = fetch_journal_metrics(
                    api_key,
                    issn=issn,
                    source_id=source_id,
                    stdout=stdout,
                )
            metrics = metric_cache[cache_key]

        author_details = {}
        if needs_author_detail_fetch(entry):
            author_details = fetch_author_details(api_key, entry, stdout=stdout)
        if not author_details.get("all_authors"):
            author_details = merge_author_details(
                author_details,
                fetch_openalex_author_details(entry, stdout=stdout),
            )
        if not author_details.get("all_authors"):
            author_details = merge_author_details(
                author_details,
                fetch_semantic_scholar_author_details(entry, stdout=stdout),
            )

        publication_defaults = build_publication_defaults(entry, metrics, author_details)

        impact_data = match_impact_factor(
            impact_factor_rows=impact_factor_rows,
            journal=publication_defaults["journal"],
            issn=publication_defaults["issn"],
            eissn=publication_defaults["eissn"],
        )
        if impact_data:
            publication_defaults["impact_factor"] = impact_data.get("impact_factor")
            publication_defaults["impact_factor_source"] = impact_data.get("source", "Manual import")
            if not publication_defaults["journal_quartile"] and impact_data.get("quartile"):
                publication_defaults["journal_quartile"] = impact_data["quartile"]
                publication_defaults["journal_quartile_basis"] = impact_data.get(
                    "quartile_basis",
                    "Imported with impact factor dataset",
                )

        scopus_eid = publication_defaults["scopus_eid"]
        publication, created = Publication.objects.update_or_create(
            scopus_eid=scopus_eid,
            defaults=publication_defaults,
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

        stdout.write(
            f"{'Created' if created else 'Updated'}: {publication.title} "
            f"[{publication.journal_quartile or '-'} | IF {publication.impact_factor or '-'}]"
        )

    return created_count, updated_count, len(entries)


def build_author_query(author_name):
    normalized = " ".join(stringify(author_name).split())
    if not normalized:
        raise CommandError("Author name cannot be empty.")

    parts = normalized.split(" ")
    if len(parts) == 1:
        token = escape_scopus_value(parts[0])
        return f"AUTHLASTNAME({token})"

    first_name = parts[0]
    last_name = parts[-1]
    middle_names = parts[1:-1]

    last_token = escape_scopus_value(last_name)
    first_token = escape_scopus_value(first_name)

    clauses = [
        f"AUTHLASTNAME({last_token}) AND AUTHFIRST({first_token})",
        f'AUTH("{escape_scopus_value(normalized)}")',
    ]

    if middle_names:
        initials = "".join(name[0] for name in [first_name, *middle_names] if name)
        if initials:
            clauses.append(
                f"AUTHLASTNAME({last_token}) AND AUTHFIRST({escape_scopus_value(initials)})"
            )

    return "(" + " OR ".join(clauses) + ")"


def escape_scopus_value(value):
    return '"' + stringify(value).replace('"', '\\"') + '"'


def call_json_api(base_url, api_key, params, extra_headers=None):
    url = f"{base_url}?{urlencode(params)}"
    headers = {
        "Accept": "application/json",
    }
    if api_key:
        headers["X-ELS-APIKey"] = api_key
    if extra_headers:
        headers.update(extra_headers)

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise CommandError(f"HTTP {exc.code} calling {base_url}\n{body}") from exc
    except URLError as exc:
        raise CommandError(f"Network error calling {base_url}: {exc}") from exc


def build_publication_defaults(entry, metrics, author_details=None):
    author_details = author_details or {}
    author_names = extract_author_names(entry, author_details)
    all_authors = ", ".join(author_names)
    corresponding_author = extract_corresponding_author(entry, author_names, author_details)
    journal_name = stringify(entry.get("prism:publicationName"))
    cover_date = parse_date(entry.get("prism:coverDate"))
    doi = stringify(entry.get("prism:doi"))
    issn = clean_issn(entry.get("prism:issn", ""))
    eissn = clean_issn(metrics.get("eissn") or "")
    source_id = stringify(entry.get("source-id") or metrics.get("source_id"))
    eid = stringify(entry.get("eid"))

    external_url = extract_external_url(entry)

    defaults = {
        "title": stringify(entry.get("dc:title"))[:255],
        "abstract": stringify(entry.get("dc:description"))[:5000],
        "authors": (all_authors or stringify(entry.get("dc:creator")))[:255],
        "all_authors": all_authors[:5000],
        "corresponding_author": corresponding_author[:255],
        "published_date": cover_date,
        "journal": journal_name[:255],
        "keywords": stringify(entry.get("authkeywords"))[:255],
        "external_url": external_url,
        "source": "scopus",
        "scopus_eid": eid,
        "scopus_id": extract_scopus_id(entry),
        "scopus_source_id": source_id[:50],
        "doi": doi[:255],
        "issn": issn[:20],
        "eissn": eissn[:20],
        "journal_quartile": stringify(metrics.get("quartile"))[:10],
        "journal_quartile_basis": stringify(metrics.get("quartile_basis"))[:100],
        "citescore": to_decimal(metrics.get("citescore")),
        "citescore_percentile": to_decimal(metrics.get("citescore_percentile")),
        "sjr": to_decimal(metrics.get("sjr")),
        "snip": to_decimal(metrics.get("snip")),
    }
    return defaults


def extract_author_names(entry, author_details=None):
    author_details = author_details or {}
    authors = entry.get("author", [])
    if isinstance(authors, dict):
        authors = [authors]

    names = []
    for author in authors:
        if not isinstance(author, dict):
            continue
        indexed_name = stringify(author.get("authname") or author.get("ce:indexed-name"))
        given_name = stringify(author.get("given-name") or author.get("ce:given-name"))
        surname = stringify(author.get("surname") or author.get("ce:surname"))

        if indexed_name:
            names.append(indexed_name)
        elif given_name or surname:
            names.append(" ".join(part for part in [given_name, surname] if part))

    if names:
        return deduplicate_preserve_order(names)

    if author_details.get("all_authors"):
        return deduplicate_preserve_order(author_details["all_authors"])

    creator = stringify(entry.get("dc:creator"))
    if creator:
        return [creator]
    return []


def extract_corresponding_author(entry, author_names, author_details=None):
    author_details = author_details or {}
    if author_details.get("corresponding_author"):
        return author_details["corresponding_author"]

    raw_candidates = [
        scalarize(entry.get("correspondence")),
        scalarize(entry.get("corresponding-author")),
        scalarize(entry.get("correspondence-name")),
    ]
    for candidate in raw_candidates:
        text = stringify(candidate)
        if text:
            return text
    return author_names[0] if len(author_names) == 1 else ""


def needs_author_detail_fetch(entry):
    authors = entry.get("author", [])
    if isinstance(authors, list) and len(authors) > 1:
        return False
    if isinstance(authors, dict):
        return False
    return bool(stringify(entry.get("eid")))


def fetch_author_details(api_key, entry, stdout=None):
    eid = stringify(entry.get("eid"))
    if not eid:
        return {}

    url = f"{ABSTRACT_EID_URL}/{eid}"
    try:
        payload = call_json_api(
            url,
            api_key,
            {"view": "META_ABS"},
        )
    except CommandError as exc:
        message = str(exc)
        if "AUTHORIZATION_ERROR" in message:
            if stdout is not None:
                stdout.write(
                    f"Skipping abstract author details for {eid}: this API key is not authorized for Abstract Retrieval META_ABS."
                )
            return {}
        if stdout is not None:
            stdout.write(f"Skipping abstract author details for {eid}: {message}")
        return {}

    values = flatten_json(payload)
    author_names = extract_names_from_abstract_payload(payload)
    corresponding_author = pick_first(
        values,
        [
            "correspondence-name",
            "corresponding-author",
            "preferred-name",
        ],
    )

    return {
        "all_authors": author_names,
        "corresponding_author": stringify(corresponding_author),
    }


def fetch_openalex_author_details(entry, stdout=None):
    title = stringify(entry.get("dc:title"))
    if not title:
        return {}

    params = {
        "search": title,
        "per-page": 5,
    }
    try:
        payload = call_json_api(
            OPENALEX_WORKS_URL,
            api_key=None,
            params=params,
            extra_headers={"User-Agent": "research-center-site/1.0"},
        )
    except CommandError as exc:
        if stdout is not None:
            stdout.write(f"OpenAlex fallback failed for title lookup: {exc}")
        return {}

    candidates = payload.get("results", [])
    best = match_best_title_candidate(title, candidates, get_title=lambda item: stringify(item.get("display_name")))
    if not best:
        return {}

    author_names = []
    for authorship in best.get("authorships", []):
        author = authorship.get("author", {}) if isinstance(authorship, dict) else {}
        name = stringify(author.get("display_name"))
        if name:
            author_names.append(name)

    corresponding_author = ""
    corresponding_ids = best.get("corresponding_author_ids") or []
    if corresponding_ids:
        corresponding_target = stringify(corresponding_ids[0])
        for authorship in best.get("authorships", []):
            author = authorship.get("author", {}) if isinstance(authorship, dict) else {}
            if stringify(author.get("id")) == corresponding_target:
                corresponding_author = stringify(author.get("display_name"))
                break

    if stdout is not None and author_names:
        stdout.write(f"Filled author list from OpenAlex for: {title}")

    return {
        "all_authors": deduplicate_preserve_order(author_names),
        "corresponding_author": corresponding_author,
    }


def fetch_semantic_scholar_author_details(entry, stdout=None):
    title = stringify(entry.get("dc:title"))
    if not title:
        return {}

    params = {
        "query": title,
        "limit": 5,
        "fields": "title,authors",
    }
    try:
        payload = call_json_api(
            SEMANTIC_SCHOLAR_PAPER_SEARCH_URL,
            api_key=None,
            params=params,
            extra_headers={"User-Agent": "research-center-site/1.0"},
        )
    except CommandError as exc:
        if stdout is not None:
            stdout.write(f"Semantic Scholar fallback failed for title lookup: {exc}")
        return {}

    candidates = payload.get("data", [])
    best = match_best_title_candidate(title, candidates, get_title=lambda item: stringify(item.get("title")))
    if not best:
        return {}

    author_names = []
    for author in best.get("authors", []):
        if isinstance(author, dict):
            name = stringify(author.get("name"))
            if name:
                author_names.append(name)

    if stdout is not None and author_names:
        stdout.write(f"Filled author list from Semantic Scholar for: {title}")

    return {
        "all_authors": deduplicate_preserve_order(author_names),
        "corresponding_author": "",
    }


def merge_author_details(primary, fallback):
    merged = dict(primary or {})
    fallback = fallback or {}
    if not merged.get("all_authors") and fallback.get("all_authors"):
        merged["all_authors"] = fallback["all_authors"]
    if not merged.get("corresponding_author") and fallback.get("corresponding_author"):
        merged["corresponding_author"] = fallback["corresponding_author"]
    return merged


def match_best_title_candidate(target_title, candidates, get_title):
    normalized_target = normalize_title(target_title)
    if not normalized_target:
        return None

    exact = None
    partial = None
    for item in candidates:
        candidate_title = normalize_title(get_title(item))
        if not candidate_title:
            continue
        if candidate_title == normalized_target:
            exact = item
            break
        if normalized_target in candidate_title or candidate_title in normalized_target:
            partial = partial or item

    return exact or partial


def extract_names_from_abstract_payload(payload):
    names = []

    def walk(node):
        if isinstance(node, dict):
            if any(key in node for key in ("ce:indexed-name", "authname", "preferred-name")):
                name = stringify(
                    scalarize(node.get("ce:indexed-name"))
                    or scalarize(node.get("authname"))
                    or scalarize(node.get("preferred-name"))
                )
                if name:
                    names.append(name)
            else:
                given = stringify(scalarize(node.get("ce:given-name")) or scalarize(node.get("given-name")))
                surname = stringify(scalarize(node.get("ce:surname")) or scalarize(node.get("surname")))
                if given or surname:
                    names.append(" ".join(part for part in [given, surname] if part))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    filtered = [name for name in deduplicate_preserve_order(names) if len(name) > 2]
    return filtered


def fetch_journal_metrics(api_key, issn="", source_id="", stdout=None):
    params = {"view": "ENHANCED"}
    if issn:
        params["issn"] = issn
    elif source_id:
        params["source_id"] = source_id
    else:
        return {}

    try:
        payload = call_json_api(SERIAL_TITLE_URL, api_key, params)
    except CommandError as exc:
        message = str(exc)
        if "AUTHORIZATION_ERROR" in message:
            if stdout is not None:
                label = issn or source_id or "unknown source"
                stdout.write(
                    f"Skipping journal metrics for {label}: this API key is not authorized for Serial Title API."
                )
            return {}
        raise

    values = flatten_json(payload)

    citescore = pick_first(values, ["citeScoreCurrentMetric", "citeScore"])
    percentile = pick_first(values, ["citeScoreCurrentMetricPercentile", "percentile"])
    sjr = pick_first(values, ["SJR", "sjr"])
    snip = pick_first(values, ["SNIP", "snip"])
    quartile = pick_first(values, ["quartile", "CiteScoreQuartile"])
    quartile_basis = ""

    if quartile:
        quartile_basis = "Reported by Elsevier source metadata"
    elif percentile is not None:
        quartile = infer_quartile(percentile)
        quartile_basis = "Inferred from CiteScore percentile"

    eissn = pick_first(values, ["eIssn", "e-issn", "eissn"])
    resolved_source_id = pick_first(values, ["source-id", "sourceId"])

    return {
        "citescore": citescore,
        "citescore_percentile": percentile,
        "sjr": sjr,
        "snip": snip,
        "quartile": quartile,
        "quartile_basis": quartile_basis,
        "eissn": stringify(eissn),
        "source_id": stringify(resolved_source_id),
    }


def flatten_json(node):
    pairs = []
    if isinstance(node, dict):
        for key, value in node.items():
            pairs.append((str(key), value))
            pairs.extend(flatten_json(value))
    elif isinstance(node, list):
        for item in node:
            pairs.extend(flatten_json(item))
    return pairs


def pick_first(pairs, candidate_keys):
    lowered = [item.lower() for item in candidate_keys]
    for key, value in pairs:
        key_lower = key.lower()
        if any(token in key_lower for token in lowered):
            scalar = scalarize(value)
            if scalar not in ("", None):
                return scalar
    return None


def scalarize(value):
    if isinstance(value, dict):
        for nested_key in ("$", "@value", "#text", "value"):
            if nested_key in value:
                return scalarize(value[nested_key])
        return None
    if isinstance(value, list):
        for item in value:
            scalar = scalarize(item)
            if scalar not in ("", None):
                return scalar
        return None
    return value


def extract_external_url(entry):
    links = entry.get("link", [])
    if isinstance(links, dict):
        links = [links]

    for link in links:
        ref_value = stringify(link.get("@ref") or link.get("ref")).lower()
        href_value = stringify(link.get("@href") or link.get("href"))
        if ref_value == "scopus" and href_value:
            return href_value

    return stringify(entry.get("prism:url"))


def extract_scopus_id(entry):
    scopus_id = stringify(entry.get("dc:identifier"))
    if scopus_id.startswith("SCOPUS_ID:"):
        return scopus_id.replace("SCOPUS_ID:", "", 1)
    prism_url = stringify(entry.get("prism:url"))
    if prism_url:
        return prism_url.rstrip("/").split("/")[-1]
    return ""


def parse_date(value):
    text = stringify(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def to_decimal(value):
    scalar = stringify(value)
    if not scalar:
        return None
    try:
        return Decimal(str(scalar))
    except (InvalidOperation, TypeError):
        return None


def stringify(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_issn(value):
    text = stringify(value).upper().replace(" ", "")
    if not text:
        return ""
    if "-" in text:
        return text
    if len(text) == 8:
        return f"{text[:4]}-{text[4:]}"
    return text


def infer_quartile(percentile):
    try:
        value = Decimal(str(percentile))
    except InvalidOperation:
        return ""
    if value >= Decimal("75"):
        return "Q1"
    if value >= Decimal("50"):
        return "Q2"
    if value >= Decimal("25"):
        return "Q3"
    return "Q4"


def load_impact_factor_csv(path_value):
    if not path_value:
        return []

    path = Path(path_value)
    if not path.exists():
        raise CommandError(f"Impact factor CSV not found: {path}")

    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row = {normalize_header(key): (value or "").strip() for key, value in raw_row.items()}
            rows.append(row)
    return rows


def match_impact_factor(impact_factor_rows, journal, issn, eissn):
    if not impact_factor_rows:
        return None

    journal_key = normalize_text(journal)
    issn_key = clean_issn(issn)
    eissn_key = clean_issn(eissn)

    for row in impact_factor_rows:
        row_issn = clean_issn(row.get("issn") or row.get("printissn") or row.get("issnprint"))
        row_eissn = clean_issn(row.get("eissn") or row.get("onlineissn"))
        row_title = normalize_text(row.get("journal") or row.get("journaltitle") or row.get("title"))

        matched = False
        if issn_key and issn_key in {row_issn, row_eissn}:
            matched = True
        elif eissn_key and eissn_key in {row_issn, row_eissn}:
            matched = True
        elif journal_key and journal_key == row_title:
            matched = True

        if matched:
            impact_factor = first_non_empty(
                row.get("impactfactor"),
                row.get("jif"),
                row.get("journalimpactfactor"),
            )
            quartile = first_non_empty(
                row.get("quartile"),
                row.get("jifquartile"),
                row.get("journalquartile"),
            )
            source = first_non_empty(row.get("source"), "Imported impact factor CSV")
            return {
                "impact_factor": to_decimal(impact_factor),
                "quartile": quartile,
                "quartile_basis": "Imported with impact factor dataset",
                "source": source,
            }
    return None


def normalize_header(value):
    return re.sub(r"[^a-z0-9]", "", stringify(value).lower())


def normalize_text(value):
    text = stringify(value).lower()
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(value):
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def first_non_empty(*values):
    for value in values:
        if stringify(value):
            return stringify(value)
    return ""


def deduplicate_preserve_order(values):
    seen = set()
    result = []
    for value in values:
        key = stringify(value)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result
