import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.projects.models import ProjectCategory, ResearchProject


HEADER_SYNONYMS = {
    "title": ["เธเธทเนเธญเนเธเธฃเธเธเธฒเธฃ", "เธเธทเนเธญเนเธเธฃเธเธเธชเธฃ", "project_title", "project title"],
    "pi_name": ["เธเธทเนเธญ-เธชเธเธธเธฅ เธซเธฑเธงเธซเธเนเธฒเนเธเธฃเธเธเธฒเธฃ", "เธเธทเนเธญเธชเธเธธเธฅเธซเธฑเธงเธซเธเนเธฒเนเธเธฃเธเธเธฒเธฃ", "เธซเธฑเธงเธซเธเนเธฒเนเธเธฃเธเธเธฒเธฃ", "pi_name"],
    "pi_org": ["เธชเธฑเธเธเธฑเธ” เธซเธฑเธงเธซเธเนเธฒเนเธเธฃเธเธเธฒเธฃ", "เธชเธฑเธเธเธฑเธ”เธซเธฑเธงเธซเธเนเธฒเนเธเธฃเธเธเธฒเธฃ", "เธซเธฑเธงเธซเธเนเธฒเธซเธเนเธงเธขเธเธฒเธ", "pi_org"],
    "funder_name": ["เธเธทเนเธญเนเธซเธฅเนเธเธ—เธธเธ", "เนเธซเธฅเนเธเธ—เธธเธ", "funder_name"],
    "funder_type": ["เธเธฃเธฐเน€เธ เธ—เนเธซเธฅเนเธเธ—เธธเธ", "เธเธฃเธฐเน€เธ เธ—เนเธซเธฅเนเธเธ—เธธเธ(เนเธเธเธฃเธฐเน€เธ—เธจ/เธเธญเธเธเธฃเธฐเน€เธ—เธจ)", "funder_type"],
    "budget": ["เธเธเธเธฃเธฐเธกเธฒเธ“ (เธเธฒเธ—)", "เธเธเธเธฃเธฐเธกเธฒเธ“", "budget"],
    "start_date": ["เธงเธฑเธเน€เธฃเธดเนเธกเธ•เนเธ", "เธงเธฑเธเธ—เธตเนเน€เธฃเธดเนเธกเธ•เนเธ", "start_date"],
    "end_date": ["เธงเธฑเธเธชเธดเนเธเธชเธธเธ”", "เธงเธฑเธเธ—เธตเนเธชเธดเนเธเธชเธธเธ”", "end_date"],
    "duration_year": ["เธฃเธฐเธขเธฐเน€เธงเธฅเธฒเธ”เธณเน€เธเธดเธเธเธฒเธ (เธเธต เธ.เธจ.)", "เธเธตเธเธเธเธฃเธฐเธกเธฒเธ“", "fiscal_year"],
    "project_code": ["เธฃเธซเธฑเธชเนเธเธฃเธเธเธฒเธฃ", "project_code"],
    "cmu_mis": ["cmu mis", "cmu_mis"],
}


CATEGORY_KEYWORDS = {
    "smart-agriculture-future-food": {
        "name": "Smart Agriculture and Future Food",
        "color": "#4f9f36",
        "icon": "AG",
        "map_x": 18,
        "map_y": 16,
        "keywords": ["farm", "agri", "food", "crop", "livestock", "supply chain"],
    },
    "energy-environment-sustainability": {
        "name": "Energy, Environment and Sustainability",
        "color": "#1f5f9f",
        "icon": "EN",
        "map_x": 43,
        "map_y": 15,
        "keywords": ["energy", "power", "electric", "environment", "climate", "carbon", "sustain"],
    },
    "ai-digital-intelligent-technology": {
        "name": "AI, Digital and Intelligent Technology",
        "color": "#6d48c7",
        "icon": "AI",
        "map_x": 66,
        "map_y": 16,
        "keywords": ["ai", "digital", "data", "analytics", "algorithm", "nlp", "machine learning"],
    },
    "economy-finance-forecasting": {
        "name": "Economy, Finance and Forecasting",
        "color": "#be7b1b",
        "icon": "EC",
        "map_x": 85,
        "map_y": 26,
        "keywords": ["econom", "finance", "forecast", "budget", "fdi", "investment", "macro"],
    },
    "health-society-wellbeing": {
        "name": "Health, Society and Wellbeing",
        "color": "#c04f67",
        "icon": "HL",
        "map_x": 14,
        "map_y": 52,
        "keywords": ["health", "wellbeing", "social", "covid", "hospital", "public health"],
    },
    "water-regional-environment-management": {
        "name": "Water and Regional Environment Management",
        "color": "#4aa7b3",
        "icon": "WT",
        "map_x": 88,
        "map_y": 50,
        "keywords": ["water", "flood", "drought", "watershed", "basin", "regional environment"],
    },
    "policy-science-institutional-development": {
        "name": "Policy, Science and Institutional Development",
        "color": "#2d66a9",
        "icon": "PL",
        "map_x": 16,
        "map_y": 75,
        "keywords": ["policy", "institution", "science", "regulation", "governance"],
    },
    "community-economy-high-value-supply-chain": {
        "name": "Community Economy and High-Value Supply Chain",
        "color": "#c5932f",
        "icon": "CM",
        "map_x": 40,
        "map_y": 74,
        "keywords": ["community", "market", "value chain", "sme", "local economy"],
    },
    "impact-assessment-public-policy": {
        "name": "Impact Assessment and Public Policy",
        "color": "#4b5f78",
        "icon": "IA",
        "map_x": 58,
        "map_y": 84,
        "keywords": ["impact", "evaluation", "public policy", "ex-ante", "economic impact", "social impact"],
    },
    "data-infrastructure-smart-city": {
        "name": "Data Infrastructure and Smart City",
        "color": "#5b9a3b",
        "icon": "DT",
        "map_x": 82,
        "map_y": 83,
        "keywords": ["smart city", "platform", "data infrastructure", "trading system", "iot"],
    },
}

class Command(BaseCommand):
    help = "Import research projects from CSV file into ResearchProject model."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to CSV file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and preview without saving to database",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"]).expanduser().resolve()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")
        if file_path.suffix.lower() != ".csv":
            raise CommandError("Only CSV files are supported. Please export your Excel file to CSV first.")

        rows = load_csv_rows(file_path)
        if not rows:
            raise CommandError("CSV file has no data rows.")

        mapped_rows = [map_row_keys(row) for row in rows]
        self.stdout.write(f"Loaded {len(mapped_rows)} rows from {file_path.name}")

        create_count = 0
        update_count = 0
        skipped_count = 0

        with transaction.atomic():
            for index, row in enumerate(mapped_rows, start=1):
                title = clean_text(row.get("title"))
                if not title:
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f"Row {index}: skipped (missing project title)"))
                    continue

                category = get_or_create_category_for_title(title)
                slug = build_unique_slug(title)
                fiscal_year = extract_fiscal_year(row)
                status = infer_status(row, fiscal_year)

                project_defaults = {
                    "category": category,
                    "fiscal_year": fiscal_year,
                    "funding_source": build_funding_source(row),
                    "principal_investigator": clean_text(row.get("pi_name")) or "-",
                    "co_investigators": build_co_investigator_text(row),
                    "budget_amount": extract_budget(row),
                    "project_code": clean_text(row.get("project_code")),
                    "cmu_mis_code": clean_text(row.get("cmu_mis")),
                    "imported_start_date_text": clean_text(row.get("start_date")),
                    "imported_end_date_text": clean_text(row.get("end_date")),
                    "status": status,
                    "abstract": "",
                    "outcomes": build_outcomes(row),
                    "is_featured": False,
                    "is_published": True,
                }

                project, created = ResearchProject.objects.update_or_create(
                    title=title,
                    defaults={**project_defaults, "slug": slug},
                )

                if created:
                    create_count += 1
                else:
                    update_count += 1

                self.stdout.write(
                    f"Row {index}: {'created' if created else 'updated'} "
                    f"[{project.category.name if project.category else 'Uncategorized'}] {project.title}"
                )

            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run mode: changes were rolled back."))

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Created {create_count}, updated {update_count}, skipped {skipped_count}."
            )
        )


def load_csv_rows(path):
    encodings = ["utf-8-sig", "utf-8", "cp874", "tis-620"]
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    raise CommandError("Cannot decode CSV file. Try exporting as UTF-8 CSV.")


def normalize_header(text):
    cleaned = clean_text(text).lower()
    return re.sub(r"[^a-z0-9เธ-เน]+", "", cleaned)


def map_row_keys(raw_row):
    normalized_row = {normalize_header(key): (value or "").strip() for key, value in raw_row.items()}
    mapped = {}
    for target_key, aliases in HEADER_SYNONYMS.items():
        mapped[target_key] = ""
        for alias in aliases:
            value = normalized_row.get(normalize_header(alias), "")
            if value:
                mapped[target_key] = value
                break
    return mapped


def clean_text(value):
    return str(value or "").strip()


def extract_budget(row):
    raw = clean_text(row.get("budget"))
    if not raw:
        return 0
    cleaned = raw.replace(",", "").replace("เธเธฒเธ—", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0


def extract_fiscal_year(row):
    source = clean_text(row.get("duration_year"))
    match = re.search(r"(25\d{2}|20\d{2})", source)
    if not match:
        return 2026
    year = int(match.group(1))
    if year > 2400:
        return year - 543
    return year


def infer_status(row, fiscal_year):
    end_text = clean_text(row.get("end_date"))
    if end_text:
        if any(token in end_text for token in ["เน€เธชเธฃเนเธ", "เธเธ", "เธชเธดเนเธเธชเธธเธ”"]):
            return ResearchProject.Status.COMPLETED
    return ResearchProject.Status.COMPLETED if fiscal_year < 2026 else ResearchProject.Status.ONGOING


def build_funding_source(row):
    name = clean_text(row.get("funder_name"))
    funder_type = clean_text(row.get("funder_type"))
    if name and funder_type:
        return f"{name} ({funder_type})"
    return name or funder_type or "-"


def build_co_investigator_text(row):
    org = clean_text(row.get("pi_org"))
    return f"Lead organization: {org}" if org else ""


def build_outcomes(row):
    parts = []
    code = clean_text(row.get("project_code"))
    cmu_mis = clean_text(row.get("cmu_mis"))
    start_date = clean_text(row.get("start_date"))
    end_date = clean_text(row.get("end_date"))
    if code:
        parts.append(f"Project code: {code}")
    if cmu_mis:
        parts.append(f"CMU MIS: {cmu_mis}")
    if start_date or end_date:
        parts.append(f"Timeline: {start_date or '-'} to {end_date or '-'}")
    return "\n".join(parts)


def get_or_create_category_for_title(title):
    title_lower = title.lower()
    for slug, config in CATEGORY_KEYWORDS.items():
        if any(keyword in title_lower for keyword in config["keywords"]):
            category, _ = ProjectCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": config["name"],
                    "color": config["color"],
                    "icon": config["icon"],
                    "map_x": config["map_x"],
                    "map_y": config["map_y"],
                    "description": f"Auto-generated category for {config['name']}.",
                    "is_active": True,
                },
            )
            return category

    category, _ = ProjectCategory.objects.get_or_create(
        slug="general-research",
        defaults={
            "name": "General Research",
            "color": "#64748b",
            "icon": "๐“",
            "map_x": 50,
            "map_y": 50,
            "description": "Projects that need manual category mapping.",
            "is_active": True,
        },
    )
    return category


def build_unique_slug(title):
    base_slug = slugify(title, allow_unicode=False)[:220] or "project"
    slug = base_slug
    suffix = 2
    while ResearchProject.objects.filter(slug=slug).exclude(title=title).exists():
        slug = f"{base_slug[:210]}-{suffix}"
        suffix += 1
    return slug

