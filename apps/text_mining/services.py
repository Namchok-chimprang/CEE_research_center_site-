import re
from math import log
from collections import Counter

from django.utils import timezone

from apps.publications.models import Publication

from .models import PublicationTextMining, TextMiningRun

SOURCE_FIELD_CHOICES = [
    ("title", "Title"),
    ("abstract", "Abstract"),
    ("keywords", "Keywords"),
    ("authors", "Authors"),
    ("all_authors", "All Authors"),
    ("journal", "Journal"),
    ("sdg_goals", "SDG Goals"),
]

FIELD_ACCESSORS = {
    "title": lambda publication: publication.title or "",
    "abstract": lambda publication: publication.abstract or "",
    "keywords": lambda publication: publication.keywords or "",
    "authors": lambda publication: publication.authors or "",
    "all_authors": lambda publication: publication.all_authors or "",
    "journal": lambda publication: publication.journal or "",
    "sdg_goals": lambda publication: publication.sdg_goals or "",
}

TOPIC_KEYWORDS = {
    "Econometrics": {
        "econometric",
        "econometrics",
        "regression",
        "regressions",
        "panel",
        "causality",
        "forecast",
        "forecasting",
        "time",
        "series",
        "cointegration",
        "estimation",
        "quantile",
        "variance",
        "volatility",
        "economy",
        "เศรษฐมิติ",
        "การพยากรณ์",
        "การประมาณ",
    },
    "Agriculture": {
        "agricultural",
        "agriculture",
        "crop",
        "crops",
        "farmer",
        "farmers",
        "farming",
        "food",
        "rice",
        "livestock",
        "land",
        "rural",
        "agro",
        "ข้าว",
        "เกษตร",
        "เกษตรกร",
        "การเกษตร",
    },
    "Policy": {
        "policy",
        "policies",
        "governance",
        "regulation",
        "regulatory",
        "public",
        "institution",
        "institutions",
        "reform",
        "government",
        "นโยบาย",
        "ภาครัฐ",
        "รัฐ",
        "มาตรการ",
    },
    "Development": {
        "development",
        "inequality",
        "education",
        "health",
        "poverty",
        "employment",
        "income",
        "welfare",
        "household",
        "community",
        "การพัฒนา",
        "ความเหลื่อมล้ำ",
        "ชุมชน",
        "ครัวเรือน",
    },
    "Sustainability": {
        "climate",
        "carbon",
        "environment",
        "environmental",
        "sustainable",
        "sustainability",
        "green",
        "energy",
        "water",
        "sdg",
        "สิ่งแวดล้อม",
        "พลังงาน",
        "ยั่งยืน",
        "คาร์บอน",
    },
}

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z\-']{2,}|[\u0E00-\u0E7F]{2,}")
STOPWORDS = {
    "a",
    "about",
    "across",
    "an",
    "after",
    "also",
    "amongst",
    "and",
    "are",
    "as",
    "at",
    "among",
    "analysis",
    "approach",
    "be",
    "because",
    "based",
    "by",
    "between",
    "center",
    "can",
    "could",
    "data",
    "do",
    "does",
    "effect",
    "effects",
    "evidence",
    "for",
    "found",
    "from",
    "has",
    "have",
    "how",
    "in",
    "is",
    "it",
    "into",
    "journal",
    "may",
    "more",
    "model",
    "models",
    "of",
    "on",
    "or",
    "our",
    "paper",
    "papers",
    "show",
    "shows",
    "such",
    "research",
    "results",
    "study",
    "studies",
    "than",
    "that",
    "the",
    "them",
    "their",
    "these",
    "this",
    "those",
    "through",
    "to",
    "toward",
    "under",
    "use",
    "using",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "will",
    "within",
    "with",
    "งานวิจัย",
    "ศึกษา",
    "การศึกษา",
    "และ",
    "ของ",
    "ใน",
    "ที่",
    "เป็น",
    "โดย",
    "ต่อ",
    "เพื่อ",
    "จาก",
    "กับ",
    "หรือ",
    "ซึ่ง",
    "นี้",
    "นั้น",
    "ได้",
    "ให้",
    "มี",
    "ไม่มี",
    "มาก",
    "น้อย",
    "ผ่าน",
    "ใช้",
    "การ",
    "ด้าน",
    "เรื่อง",
    "ผล",
    "ผลการ",
    "ข้อมูล",
    "แบบจำลอง",
    "โมเดล",
    "บทความ",
    "วารสาร",
    "ฉบับ",
    "ศูนย์",
    "ความ",
    "งาน",
    "วิจัย",
}


def normalize_source_fields(source_fields):
    values = source_fields or ["title", "abstract"]
    normalized = [field for field in values if field in FIELD_ACCESSORS]
    return normalized or ["title", "abstract"]


def build_publication_source_text(publication, source_fields):
    parts = [
        FIELD_ACCESSORS[field](publication).strip()
        for field in normalize_source_fields(source_fields)
        if FIELD_ACCESSORS[field](publication).strip()
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def tokenize_text(value):
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(value or "")]
    return [token for token in tokens if token not in STOPWORDS]


def extract_bigrams(tokens, limit=5):
    pairs = [
        f"{left} {right}"
        for left, right in zip(tokens, tokens[1:])
        if left != right
    ]
    return [{"term": term, "count": count} for term, count in Counter(pairs).most_common(limit)]


def classify_topics(token_counts, tfidf_scores):
    topic_scores = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum((token_counts.get(keyword, 0) * 0.35) + tfidf_scores.get(keyword, 0.0) for keyword in keywords)
        if score > 0:
            topic_scores.append({"topic": topic, "score": round(score, 3)})
    topic_scores.sort(key=lambda item: (-item["score"], item["topic"]))
    primary_topic = topic_scores[0]["topic"] if topic_scores else "General"
    if not topic_scores:
        topic_scores.append({"topic": "General", "score": 0})
    return primary_topic, topic_scores


def build_document_frequencies(token_lists):
    document_frequencies = Counter()
    for tokens in token_lists:
        document_frequencies.update(set(tokens))
    return document_frequencies


def build_tfidf_scores(tokens, document_frequencies, total_documents):
    token_counts = Counter(tokens)
    if not token_counts:
        return token_counts, {}

    max_count = max(token_counts.values()) or 1
    tfidf_scores = {}
    for token, count in token_counts.items():
        tf = 0.5 + 0.5 * (count / max_count)
        idf = log((1 + total_documents) / (1 + document_frequencies[token])) + 1
        tfidf_scores[token] = tf * idf
    return token_counts, tfidf_scores


def top_terms_from_tfidf(token_counts, tfidf_scores, limit=8):
    ranked_terms = sorted(
        tfidf_scores.items(),
        key=lambda item: (-item[1], -token_counts[item[0]], item[0]),
    )[:limit]
    return [
        {
            "term": term,
            "score": round(score, 4),
            "count": token_counts[term],
        }
        for term, score in ranked_terms
    ]


def aggregate_ranked_terms(per_publication_terms, limit=12):
    aggregate_scores = Counter()
    aggregate_counts = Counter()
    for item in per_publication_terms:
        for term in item["dominant_terms"]:
            aggregate_scores[term["term"]] += term["score"]
            aggregate_counts[term["term"]] += term["count"]
    ranked = sorted(
        aggregate_scores.items(),
        key=lambda pair: (-pair[1], -aggregate_counts[pair[0]], pair[0]),
    )[:limit]
    return [
        {
            "term": term,
            "score": round(score, 4),
            "count": aggregate_counts[term],
        }
        for term, score in ranked
    ]


def summarize_publication(publication, top_terms, source_fields, primary_topic):
    field_label = ", ".join(normalize_source_fields(source_fields))
    if top_terms:
        top_term_names = ", ".join(item["term"] for item in top_terms[:3])
        return (
            f"Top terms for '{publication.title}' emphasize {top_term_names}. "
            f"Primary topic: {primary_topic}. Source fields: {field_label}."
        )
    return (
        f"No strong terms were extracted for '{publication.title}'. "
        f"Source fields used: {field_label}."
    )


def analyze_publication(publication, source_fields):
    normalized_fields = normalize_source_fields(source_fields)
    source_text = build_publication_source_text(publication, normalized_fields)
    tokens = tokenize_text(source_text)
    return {
        "publication": publication,
        "source_text": source_text,
        "tokens": tokens,
        "token_count": len(tokens),
        "unique_token_count": len(set(tokens)),
    }


def finalize_publication_analysis(publication_data, source_fields, document_frequencies, total_documents):
    publication = publication_data["publication"]
    normalized_fields = normalize_source_fields(source_fields)
    token_counts, tfidf_scores = build_tfidf_scores(
        publication_data["tokens"],
        document_frequencies,
        total_documents,
    )
    top_terms = top_terms_from_tfidf(token_counts, tfidf_scores)
    primary_topic, topic_scores = classify_topics(token_counts, tfidf_scores)
    keywords = ", ".join(item["term"] for item in top_terms[:5])
    return {
        "publication": publication,
        "source_text": publication_data["source_text"],
        "token_count": publication_data["token_count"],
        "unique_token_count": publication_data["unique_token_count"],
        "primary_topic": primary_topic,
        "topic_scores": topic_scores,
        "dominant_terms": top_terms,
        "dominant_bigrams": extract_bigrams(publication_data["tokens"]),
        "generated_keywords": keywords,
        "summary": summarize_publication(publication, top_terms, normalized_fields, primary_topic),
    }


def run_text_mining(
    publications,
    initiated_by=None,
    title=None,
    scope=TextMiningRun.SCOPE_SELECTED,
    source_fields=None,
):
    publication_list = list(publications)
    normalized_fields = normalize_source_fields(source_fields)
    run = TextMiningRun.objects.create(
        title=title or f"Text mining run {timezone.now():%Y-%m-%d %H:%M}",
        scope=scope,
        status=TextMiningRun.STATUS_RUNNING,
        publication_count=len(publication_list),
        source_fields=normalized_fields,
        started_at=timezone.now(),
        initiated_by=initiated_by,
    )

    try:
        topic_counter = Counter()
        publication_inputs = []
        completed_analyses = []
        result_objects = []

        for publication in publication_list:
            publication_inputs.append(analyze_publication(publication, normalized_fields))

        document_frequencies = build_document_frequencies(
            item["tokens"] for item in publication_inputs
        )
        total_documents = len(publication_inputs) or 1

        for publication_input in publication_inputs:
            analysis = finalize_publication_analysis(
                publication_input,
                normalized_fields,
                document_frequencies,
                total_documents,
            )
            completed_analyses.append(analysis)
            topic_counter.update({analysis["primary_topic"]: 1})
            result_objects.append(
                PublicationTextMining(
                    publication=analysis["publication"],
                    run=run,
                    source_text=analysis["source_text"],
                    token_count=analysis["token_count"],
                    unique_token_count=analysis["unique_token_count"],
                    primary_topic=analysis["primary_topic"],
                    topic_scores=analysis["topic_scores"],
                    dominant_terms=analysis["dominant_terms"],
                    dominant_bigrams=analysis["dominant_bigrams"],
                    generated_keywords=analysis["generated_keywords"],
                    summary=analysis["summary"],
                )
            )

        PublicationTextMining.objects.bulk_create(result_objects)
        run.top_terms = aggregate_ranked_terms(completed_analyses)
        run.topic_summary = [
            {"topic": topic, "count": count}
            for topic, count in topic_counter.most_common()
        ]
        run.analyzed_count = len(result_objects)
        run.status = TextMiningRun.STATUS_COMPLETED
        run.finished_at = timezone.now()
        run.notes = f"Completed from Django admin using fields: {', '.join(normalized_fields)}."
        run.save(
            update_fields=[
                "source_fields",
                "top_terms",
                "topic_summary",
                "analyzed_count",
                "status",
                "finished_at",
                "notes",
                "updated_at",
            ]
        )
    except Exception as exc:
        run.status = TextMiningRun.STATUS_FAILED
        run.error_message = str(exc)
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at", "updated_at"])
        raise

    return run


def run_text_mining_for_all_publications(initiated_by=None, source_fields=None, title=None):
    publications = Publication.objects.all()
    return run_text_mining(
        publications,
        initiated_by=initiated_by,
        title=title or "Analyze all publications",
        scope=TextMiningRun.SCOPE_ALL,
        source_fields=source_fields,
    )
