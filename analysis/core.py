from __future__ import annotations

import csv
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from models.state import DataSourceResult, FileResult, Finding
from tools.filesystem_tools import list_directory_robust, read_text_file
from utils.strings import shorten, slugify_filename

QueryFn = Callable[[str, int], list[dict[str, Any]]]
SearchFn = Callable[[str, int], list[dict[str, Any]]]

SOURCE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".scala": "Scala",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".sh": "Shell",
    ".r": "R",
    ".jl": "Julia",
}

DOCUMENT_EXTENSIONS = {".md", ".txt", ".rst", ".pdf", ".docx", ".doc", ".odt", ".html", ".htm"}
DATA_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".xml", ".yaml", ".yml", ".parquet", ".feather", ".xlsx", ".xls"}
CONFIG_EXTENSIONS = {".env", ".toml", ".ini", ".cfg", ".conf", ".properties"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".mp4", ".mp3", ".wav", ".m4a"}

SENSITIVE_KEYWORDS: dict[str, list[str]] = {
    "pii": ["name", "email", "phone", "address", "ip", "ssn", "passport", "dob", "birth"],
    "protected": ["race", "ethnicity", "gender", "sex", "religion", "nationality", "disability", "age"],
    "biometric": ["face", "fingerprint", "iris", "voice", "gait", "biometric", "embedding"],
    "health": ["health", "medical", "diagnosis", "condition", "prescription", "patient"],
    "financial": ["salary", "income", "credit", "loan", "bank", "account", "payment"],
    "behavioral": ["location", "gps", "lat", "lon", "cookie", "session", "click", "behavior"],
    "legal": ["criminal", "arrest", "conviction", "offense", "court", "judgment"],
    "political": ["vote", "party", "political", "affiliation", "union", "membership"],
    "children": ["child", "children", "minor", "student", "kid", "school"],
}

RULES: list[dict[str, Any]] = [
    {
        "code": "BIO-001",
        "title": "Biometric surveillance workflow detected",
        "severity": "HIGH",
        "query": "biometric surveillance facial recognition authorisation consent",
        "primary": ["face", "facial", "biometric", "fingerprint", "iris", "voiceprint"],
        "context": ["surveillance", "recognition", "identify", "tracking", "watchlist"],
        "regulations": ["EU AI Act Article 5", "GDPR Article 9"],
        "jurisdictions": ["European Union"],
    },
    {
        "code": "EMP-001",
        "title": "Protected attributes used in automated employment context",
        "severity": "HIGH",
        "query": "automated hiring decision using demographic attributes gender age",
        "primary": ["hiring", "recruit", "applicant", "resume", "employment", "candidate"],
        "context": ["gender", "age", "race", "ethnicity", "disability", "zip code", "zipcode"],
        "regulations": ["EU AI Act Article 10", "GDPR Article 22", "US EEOC guidance"],
        "jurisdictions": ["European Union", "United States"],
    },
    {
        "code": "FIN-001",
        "title": "Automated credit or eligibility scoring with sensitive features",
        "severity": "HIGH",
        "query": "credit scoring AI protected demographic attributes fairness",
        "primary": ["credit", "loan", "underwriting", "eligibility", "score", "fraud"],
        "context": ["gender", "age", "race", "ethnicity", "income", "salary", "zip code", "zipcode"],
        "regulations": ["EU AI Act Annex III", "ECOA/Regulation B"],
        "jurisdictions": ["European Union", "United States"],
    },
    {
        "code": "DATA-001",
        "title": "Scraped or weakly governed data collection pattern",
        "severity": "MEDIUM",
        "query": "scraped internet data AI training consent violation",
        "primary": ["scrape", "crawler", "selenium", "beautifulsoup", "playwright", "harvest"],
        "context": ["dataset", "train", "model", "profile", "users", "social"],
        "regulations": ["GDPR fairness and transparency principles", "FTC unfairness guidance"],
        "jurisdictions": ["European Union", "United States"],
    },
    {
        "code": "PII-001",
        "title": "Sensitive personal data appears in ML pipeline",
        "severity": "MEDIUM",
        "query": "personal data used for machine learning without safeguards",
        "primary": ["dataset", "train", "model", "inference", "feature", "label"],
        "context": ["email", "phone", "ssn", "passport", "medical", "patient", "location"],
        "regulations": ["GDPR Articles 5 and 25", "OECD AI Principles"],
        "jurisdictions": ["European Union", "Global"],
    },
    {
        "code": "CHD-001",
        "title": "Children's data or minors appear in AI workflow",
        "severity": "HIGH",
        "query": "children data AI training consent COPPA GDPR Article 8",
        "primary": ["child", "children", "minor", "student", "school"],
        "context": ["dataset", "train", "model", "predict", "classify"],
        "regulations": ["COPPA", "GDPR Article 8"],
        "jurisdictions": ["United States", "European Union"],
    },
    {
        "code": "GEN-001",
        "title": "Synthetic media generation without visible disclosure controls",
        "severity": "MEDIUM",
        "query": "generative AI synthetic media watermark disclosure requirements",
        "primary": ["deepfake", "face swap", "voice clone", "synthetic media", "avatar"],
        "context": ["generate", "model", "render", "synthesize"],
        "regulations": ["EU AI Act transparency obligations"],
        "jurisdictions": ["European Union"],
    },
    {
        "code": "DOC-001",
        "title": "No visible governance, audit, or human-oversight controls",
        "severity": "LOW",
        "query": "high risk AI system documentation logging human oversight requirements",
        "primary": ["model", "predict", "classify", "recommend", "score"],
        "context": [],
        "requires_missing": ["fairness", "bias", "audit", "human", "review", "oversight", "logging", "explain"],
        "regulations": ["ISO/IEC 42001", "NIST AI RMF"],
        "jurisdictions": ["Global", "United States"],
    },
]

URL_PATTERN = re.compile(r"https?://[^\s'\"<>]+")
PATH_PATTERN = re.compile(
    r"(?P<path>(?:\./|\.\./|/)?(?:[A-Za-z0-9_.-]+/)*(?:data|dataset|datasets|models|artifacts|outputs|knowledge|reports)[A-Za-z0-9_./-]*\.(?:csv|tsv|json|jsonl|yaml|yml|parquet|feather|xlsx|xls|txt|md))",
    re.IGNORECASE,
)
QUOTED_PATH_PATTERN = re.compile(r"['\"]([^'\" ]+\.(?:csv|tsv|json|jsonl|yaml|yml|parquet|feather|xlsx|xls))['\"]", re.IGNORECASE)


def categorize_file(path: str | Path, mime_type: str | None = None) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix in SOURCE_EXTENSIONS:
        return "source_code"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in DATA_EXTENSIONS:
        return "structured_data"
    if suffix in CONFIG_EXTENSIONS or file_path.name in {"Dockerfile", "docker-compose.yml"}:
        return "config"
    if suffix in IMAGE_EXTENSIONS:
        return "image_media"
    if mime_type:
        if mime_type.startswith(("image/", "video/", "audio/")):
            return "image_media"
        if "text" in mime_type or "json" in mime_type or "xml" in mime_type:
            return "document"
    guessed, _ = mimetypes.guess_type(str(file_path))
    if guessed and guessed.startswith("text/"):
        return "document"
    return "binary_unknown"


def detect_language(path: str | Path) -> str | None:
    return SOURCE_EXTENSIONS.get(Path(path).suffix.lower())


def _read_docx(path: Path) -> str:
    try:
        from docx import Document

        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
    except Exception:
        return ""


def load_analysis_text(path: str | Path, file_type: str, max_chars: int | None = 120000) -> str:
    file_path = Path(path)
    if file_type == "document" and file_path.suffix.lower() == ".docx":
        text = _read_docx(file_path)
        if text:
            return text if max_chars is None else text[:max_chars]
    try:
        text = read_text_file(file_path)
        return text if max_chars is None else text[:max_chars]
    except Exception:
        return ""


def infer_schema_fields(content: str, file_path: str | Path, file_type: str) -> list[str]:
    path = Path(file_path)
    try:
        if file_type == "structured_data" and path.suffix.lower() in {".csv", ".tsv"}:
            delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
            first_line = content.splitlines()[0] if content.splitlines() else ""
            return [field.strip() for field in csv.reader([first_line], delimiter=delimiter).__next__() if field.strip()]
        if file_type == "structured_data" and path.suffix.lower() in {".json", ".jsonl"}:
            first_line = content.splitlines()[0] if content.splitlines() else "{}"
            payload = json.loads(first_line)
            if isinstance(payload, dict):
                return [str(key) for key in payload.keys()]
        if file_type in {"source_code", "config"}:
            matches = re.findall(r"([A-Za-z_][A-Za-z0-9_]{2,})\s*[:=]", content)
            return sorted(set(matches))[:30]
    except Exception:
        return []
    return []


def identify_sensitive_fields(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for keywords in SENSITIVE_KEYWORDS.values():
        for keyword in keywords:
            if keyword in lowered and keyword not in found:
                found.append(keyword)
    return found


def extract_data_sources(content: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    sources: list[dict[str, Any]] = []

    for match in URL_PATTERN.finditer(content or ""):
        source = match.group(0).rstrip(".,)")
        if source not in seen:
            seen.add(source)
            sources.append({"url_or_path": source, "source_type": "url", "context": shorten(match.group(0), 120)})

    for pattern in (PATH_PATTERN, QUOTED_PATH_PATTERN):
        for match in pattern.finditer(content or ""):
            source = match.group("path") if "path" in match.groupdict() else match.group(1)
            if source not in seen:
                seen.add(source)
                sources.append({"url_or_path": source, "source_type": "local_path", "context": shorten(match.group(0), 120)})

    return sources


def _find_first_line(content: str, keywords: list[str]) -> int | None:
    lines = content.splitlines()
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for index, line in enumerate(lines, start=1):
        lowered = line.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            return index
    return None


def _query_rag(query_rag: QueryFn | None, description: str, top_k: int) -> list[dict[str, Any]]:
    if not query_rag:
        return []
    try:
        return query_rag(description, top_k)
    except Exception:
        return []


def _build_explanation(rule: dict[str, Any], hits: list[str], file_type: str, file_path: str) -> str:
    hit_list = ", ".join(sorted(set(hits[:6])))
    return (
        f"{Path(file_path).name} contains indicators for '{rule['title'].lower()}', including: {hit_list}. "
        f"This appears in a {file_type.replace('_', ' ')} context and may trigger the listed regulations if deployed without documented safeguards."
    )


def _build_finding(
    index: int,
    rule: dict[str, Any],
    file_path: str,
    line_number: int | None,
    explanation: str,
    rag_hits: list[dict[str, Any]],
) -> Finding:
    first_hit = rag_hits[0] if rag_hits else {}
    metadata = first_hit.get("metadata", {}) if isinstance(first_hit, dict) else {}
    return {
        "id": f"F{index:03d}",
        "title": rule["title"],
        "severity": rule["severity"],
        "file_path": file_path,
        "start_line": line_number,
        "end_line": line_number,
        "section_desc": f"Line {line_number}" if line_number else "File-level heuristic",
        "regulations": list(rule["regulations"]),
        "jurisdictions": list(rule["jurisdictions"]),
        "explanation": explanation,
        "rag_chunk_id": metadata.get("chunk_id") if metadata else None,
        "rag_page": metadata.get("page") if metadata else None,
    }


def _status_from_findings(findings: list[Finding]) -> str:
    severities = {finding["severity"] for finding in findings}
    if "HIGH" in severities:
        return "FAIL"
    if "MEDIUM" in severities:
        return "WARN"
    return "PASS"


def _summarize(path: Path, file_type: str, content: str, fields: list[str], sources: list[dict[str, Any]]) -> str:
    if file_type == "source_code":
        language = detect_language(path) or "source"
        signals = []
        lowered = content.lower()
        if any(token in lowered for token in ["train", "fit(", "fine_tune", "gradient"]):
            signals.append("model training")
        if any(token in lowered for token in ["predict", "inference", "serve", "endpoint"]):
            signals.append("inference or scoring")
        if any(token in lowered for token in ["scrape", "crawler", "requests.get", "beautifulsoup", "selenium"]):
            signals.append("data collection")
        if not signals:
            signals.append("general application logic")
        return f"{path.name} is {language} code that appears to implement {', '.join(signals)}. It exposes {len(fields)} recognizable fields and references {len(sources)} explicit data sources."
    if file_type == "structured_data":
        if fields:
            return f"{path.name} looks like structured data with schema fields such as {', '.join(fields[:6])}. The sample suggests {len(fields)} tracked attributes."
        return f"{path.name} appears to be structured data, but the schema could not be confidently inferred from the sampled content."
    if file_type == "config":
        return f"{path.name} appears to be configuration for an AI or data-processing workflow. It references {len(sources)} data or service endpoints."
    if file_type == "document":
        preview = shorten(content.replace("\n", " "), 180)
        return f"{path.name} is a document-like file. Sampled content: {preview}" if preview else f"{path.name} is a document-like file that could not be summarized from text extraction."
    return f"{path.name} was categorized as {file_type.replace('_', ' ')}."


def _predict_output(file_type: str, content: str, fields: list[str]) -> str | None:
    if file_type != "source_code":
        return None
    lowered = content.lower()
    if any(token in lowered for token in ["train", "fit(", "trainer", "epoch"]):
        return "This code likely trains or fine-tunes a model and writes a learned artifact or metrics output for later deployment."
    if any(token in lowered for token in ["predict", "infer", "endpoint", "fastapi", "flask"]):
        return "This code likely receives input records and returns predictions, scores, or decisions to another system or user-facing endpoint."
    if any(token in lowered for token in ["scrape", "crawler", "selenium", "beautifulsoup"]):
        return "This code likely collects or enriches external data before storing it for downstream analytics or model training."
    if fields:
        return f"This code appears to transform records with fields such as {', '.join(fields[:5])} and produce derived data or model-facing features."
    return "This code appears to process inputs and produce derived outputs, but the final deployment behavior is not explicit from static analysis alone."


def _rule_matches(rule: dict[str, Any], lowered: str, file_type: str) -> list[str]:
    primary_hits = [keyword for keyword in rule["primary"] if keyword in lowered]
    if not primary_hits:
        return []

    context_hits = [keyword for keyword in rule.get("context", []) if keyword in lowered]
    requires_missing = rule.get("requires_missing", [])
    if requires_missing:
        if any(keyword in lowered for keyword in requires_missing):
            return []
        return primary_hits
    if rule.get("context") and not context_hits:
        return []
    return primary_hits + context_hits


def analyze_file(
    file_path: str,
    file_type: str,
    config: dict[str, Any],
    query_rag: QueryFn | None = None,
) -> tuple[FileResult, list[dict[str, Any]]]:
    path = Path(file_path)

    if file_type in {"image_media", "binary_unknown"}:
        result: FileResult = {
            "file_path": file_path,
            "file_type": file_type,
            "language": detect_language(path),
            "status": "SKIPPED",
            "summary": f"{path.name} was skipped because {file_type.replace('_', ' ')} files are not analyzed deeply in this version.",
            "predicted_output": None,
            "findings": [],
            "data_sources": [],
            "report_path": None,
            "error": None,
            "notes": [],
        }
        return result, []

    content = load_analysis_text(path, file_type)
    if not content:
        result = {
            "file_path": file_path,
            "file_type": file_type,
            "language": detect_language(path),
            "status": "ERROR",
            "summary": "",
            "predicted_output": None,
            "findings": [],
            "data_sources": [],
            "report_path": None,
            "error": f"Could not read or decode {path.name}",
            "notes": ["Static analysis could not extract text from the file."],
        }
        return result, []

    fields = infer_schema_fields(content, path, file_type)
    data_sources = extract_data_sources(content)
    summary = _summarize(path, file_type, content, fields, data_sources)
    predicted_output = _predict_output(file_type, content, fields)

    lowered = content.lower()
    top_k = int(config.get("rag", {}).get("top_k", 5))
    findings: list[Finding] = []
    finding_index = 1
    for rule in RULES:
        hits = _rule_matches(rule, lowered, file_type)
        if not hits:
            continue
        line_number = _find_first_line(content, hits)
        rag_hits = _query_rag(query_rag, rule["query"], top_k)
        explanation = _build_explanation(rule, hits, file_type, file_path)
        findings.append(_build_finding(finding_index, rule, file_path, line_number, explanation, rag_hits))
        finding_index += 1

    sensitive_fields = identify_sensitive_fields("\n".join(fields) + "\n" + content[:2000])
    if file_type == "structured_data" and len(sensitive_fields) >= 3:
        rag_hits = _query_rag(query_rag, "tabular dataset containing multiple sensitive attributes for AI processing", top_k)
        findings.append(
            _build_finding(
                finding_index,
                {
                    "title": "Dataset contains several sensitive attributes",
                    "severity": "MEDIUM",
                    "regulations": ["GDPR Article 9", "OECD AI Principles"],
                    "jurisdictions": ["European Union", "Global"],
                },
                file_path,
                1,
                f"The sampled schema or records expose multiple sensitive attributes: {', '.join(sensitive_fields[:8])}. That combination warrants explicit governance before the dataset is used in an AI pipeline.",
                rag_hits,
            )
        )
        finding_index += 1

    status = _status_from_findings(findings)
    pending_sources = [{**source, "verdict": "PENDING"} for source in data_sources]
    result = {
        "file_path": file_path,
        "file_type": file_type,
        "language": detect_language(path),
        "status": status,
        "summary": summary,
        "predicted_output": predicted_output,
        "findings": findings,
        "data_sources": [
            {
                "url_or_path": source["url_or_path"],
                "source_type": source["source_type"],
                "verdict": "PENDING",
                "publisher": None,
                "description": "Pending validation.",
                "sensitive_fields": [],
                "concerns": [],
                "regulations": [],
                "rag_citations": [],
                "path_exists": None,
                "notes": source.get("context"),
            }
            for source in data_sources
        ],
        "report_path": None,
        "error": None,
        "notes": [f"Detected fields: {', '.join(fields[:10])}" if fields else "No explicit schema fields inferred."],
    }
    return result, pending_sources


def _result_status_from_datasource(verdicts: list[str], findings: list[Finding]) -> str:
    if any(verdict == "FAIL" for verdict in verdicts):
        return "FAIL"
    if any(verdict == "WARN" for verdict in verdicts):
        return "WARN" if all(finding["severity"] != "HIGH" for finding in findings) else "FAIL"
    return _status_from_findings(findings)


def validate_data_source_reference(
    source: dict[str, Any],
    current_file: str,
    target_directory: str,
    config: dict[str, Any],
    query_rag: QueryFn | None = None,
    web_search: SearchFn | None = None,
) -> DataSourceResult:
    del current_file

    top_k = int(config.get("rag", {}).get("top_k", 5))
    url_or_path = str(source.get("url_or_path", ""))
    source_type = str(source.get("source_type", "local_path"))
    context = str(source.get("context", ""))

    verdict = "PASS"
    publisher: str | None = None
    description = ""
    concerns: list[str] = []
    sensitive_fields: list[str] = []
    regulations: list[str] = []
    rag_citations: list[dict[str, Any]] = []
    path_exists: bool | None = None
    notes: str | None = None

    if source_type == "url":
        parsed = urlparse(url_or_path)
        publisher = (parsed.netloc or "").lower().removeprefix("www.") or None
        benign_domains = {"data.gov", "github.com", "raw.githubusercontent.com", "wikipedia.org", "archive.org"}
        caution_domains = {"huggingface.co", "kaggle.com", "drive.google.com", "dropbox.com"}
        risky_domains = {"facebook.com", "instagram.com", "linkedin.com", "x.com", "twitter.com", "tiktok.com"}

        description = f"External source hosted on {publisher or 'an unknown domain'}."
        if publisher in risky_domains:
            verdict = "FAIL"
            concerns.append("Appears to rely on social or platform data where AI training and scraping permissions are commonly restricted.")
            regulations.extend(["GDPR fairness and transparency principles", "Platform terms of service restrictions"])
        elif publisher in caution_domains:
            verdict = "WARN"
            concerns.append("Dataset hosting platform identified; downstream licence and consent terms should be checked before reuse.")
            regulations.append("Licence and terms-of-use review required")
        elif publisher in benign_domains:
            verdict = "PASS"
            concerns.append("Publisher resembles a public or broadly permissive source, but downstream use still needs case-specific review.")
        else:
            verdict = "UNKNOWN"
            concerns.append("Publisher is not recognized as clearly permissive from static analysis alone.")

        if web_search:
            try:
                search_results = web_search(f"{publisher} AI training terms privacy dataset", 2)
            except Exception:
                search_results = []
            if search_results:
                notes = shorten(" | ".join(str(result.get("title") or result.get("body") or result) for result in search_results), 240)
                lowered_notes = notes.lower()
                if any(token in lowered_notes for token in ["privacy", "lawsuit", "gdpr", "consent", "breach", "copyright"]):
                    verdict = "WARN" if verdict == "PASS" else verdict
                    concerns.append("Search results surface compliance-sensitive terms that deserve manual follow-up.")

        rag_hits = _query_rag(query_rag, f"external dataset terms and provenance review for {publisher or url_or_path}", top_k)
        rag_citations = [
            {
                "chunk_id": hit.get("metadata", {}).get("chunk_id"),
                "page": hit.get("metadata", {}).get("page"),
                "text_excerpt": shorten(hit.get("text", ""), 160),
            }
            for hit in rag_hits[:3]
        ]

    else:
        candidate = Path(url_or_path)
        resolved = candidate if candidate.is_absolute() else Path(target_directory) / candidate
        path_exists = resolved.exists()
        description = f"Local source reference resolved against the scan root as {resolved}."
        sample_text = ""
        if path_exists:
            if resolved.is_dir():
                try:
                    entries = list_directory_robust(resolved, recursive=False)
                    sample_text = "\n".join(Path(str(entry["path"])).name for entry in entries[:20])
                except Exception:
                    sample_text = ""
            else:
                sample_text = load_analysis_text(resolved, categorize_file(resolved))[:5000]
        else:
            notes = "Referenced local path does not exist in the current environment; verdict is based on naming and context only."
            sample_text = f"{resolved.name} {context}"

        sensitive_fields = identify_sensitive_fields(sample_text + "\n" + resolved.name)
        if any(token in resolved.name.lower() for token in ["synthetic", "mock", "fake", "sample"]):
            verdict = "PASS"
            concerns.append("Path name suggests synthetic or sample data.")
        elif any(token in resolved.name.lower() for token in ["face", "biometric", "fingerprint", "iris"]):
            verdict = "FAIL"
            concerns.append("Path naming suggests biometric data, which is high risk without clear consent and authorization evidence.")
            regulations.extend(["EU AI Act Article 5", "GDPR Article 9"])
        elif sensitive_fields:
            verdict = "WARN"
            concerns.append(f"Sampled content or filename suggests sensitive attributes: {', '.join(sensitive_fields[:8])}.")
            regulations.extend(["GDPR Articles 5 and 9", "Data minimization and purpose limitation obligations"])
        else:
            verdict = "PASS" if path_exists else "UNKNOWN"
            concerns.append("No strong privacy or ethics signal was detected from the sampled path context.")

        rag_hits = _query_rag(query_rag, f"local dataset governance review for {resolved.name} containing {', '.join(sensitive_fields[:5])}", top_k)
        rag_citations = [
            {
                "chunk_id": hit.get("metadata", {}).get("chunk_id"),
                "page": hit.get("metadata", {}).get("page"),
                "text_excerpt": shorten(hit.get("text", ""), 160),
            }
            for hit in rag_hits[:3]
        ]

    if not regulations and rag_citations:
        regulations = ["Relevant ethics guidance retrieved from internal knowledge base"]

    return {
        "url_or_path": url_or_path,
        "source_type": source_type,
        "verdict": verdict,
        "publisher": publisher,
        "description": description,
        "sensitive_fields": sensitive_fields,
        "concerns": concerns,
        "regulations": regulations,
        "rag_citations": rag_citations,
        "path_exists": path_exists,
        "notes": notes,
    }


def merge_data_source_results(file_result: FileResult, validated_sources: list[DataSourceResult]) -> FileResult:
    findings = list(file_result.get("findings", []))
    next_id = len(findings) + 1
    for source in validated_sources:
        if source["verdict"] not in {"WARN", "FAIL"}:
            continue
        severity = "HIGH" if source["verdict"] == "FAIL" else "MEDIUM"
        citation = source["rag_citations"][0] if source.get("rag_citations") else {}
        findings.append(
            {
                "id": f"F{next_id:03d}",
                "title": f"Data source {source['verdict'].lower()}: {source['url_or_path']}",
                "severity": severity,
                "file_path": file_result["file_path"],
                "start_line": None,
                "end_line": None,
                "section_desc": "Referenced data source",
                "regulations": source.get("regulations", []),
                "jurisdictions": ["Global"],
                "explanation": shorten(" ".join(source.get("concerns", [])) or source.get("description", ""), 260),
                "rag_chunk_id": citation.get("chunk_id"),
                "rag_page": citation.get("page"),
            }
        )
        next_id += 1

    merged: FileResult = dict(file_result)
    merged["findings"] = findings
    merged["data_sources"] = validated_sources
    merged["status"] = _result_status_from_datasource([source["verdict"] for source in validated_sources], findings)
    return merged


def report_filename_for(file_path: str) -> str:
    path = Path(file_path)
    return f"{slugify_filename(path.name)}_analysis_report.md"
