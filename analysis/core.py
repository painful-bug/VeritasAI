from __future__ import annotations

import csv
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Callable

from config_loader import load_config
from models.state import FileResult
from tools.filesystem_tools import read_text_file
from utils.strings import shorten, slugify_filename

QueryFn = Callable[[str, int], list[dict[str, Any]]]

SOURCE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sh": "Shell",
}
DOCUMENT_EXTENSIONS = {".md", ".txt", ".rst", ".pdf", ".docx", ".doc", ".html", ".htm"}
DATA_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml", ".xml"}
CONFIG_EXTENSIONS = {".env", ".toml", ".ini", ".cfg", ".conf", ".properties"}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".mp4", ".mp3", ".wav"}
SCANNABLE_FILE_TYPES = {"source_code", "document", "structured_data"}
SENSITIVE_KEYWORDS = (
    "gender",
    "age",
    "race",
    "ethnicity",
    "religion",
    "disability",
    "nationality",
    "health",
    "medical",
    "diagnosis",
    "biometric",
    "face",
    "fingerprint",
    "passport",
    "ssn",
    "email",
    "phone",
    "location",
    "gps",
    "salary",
    "income",
    "credit",
    "criminal",
    "political",
    "union",
    "children",
    "minor",
    "student",
)
URL_PATTERN = re.compile(r"https?://[^\s'\"<>]+")
PATH_PATTERN = re.compile(
    r"(?P<path>(?:\./|\.\./|/)?(?:[A-Za-z0-9_.-]+/)*(?:data|dataset|datasets|models|artifacts|outputs|knowledge)[A-Za-z0-9_./-]*\.(?:csv|tsv|json|jsonl|yaml|yml|txt|md))",
    re.IGNORECASE,
)


def detect_language(path: str | Path) -> str | None:
    return SOURCE_EXTENSIONS.get(Path(path).suffix.lower())


def categorize_file(path: str | Path, file_content: str | None = None) -> str:
    candidate = Path(path)
    suffix = candidate.suffix.lower()
    if suffix in SOURCE_EXTENSIONS:
        return "source_code"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in DATA_EXTENSIONS:
        return "structured_data"
    if suffix in CONFIG_EXTENSIONS or candidate.name in {"Dockerfile", "docker-compose.yml"}:
        return "config"
    if suffix in MEDIA_EXTENSIONS:
        return "image_media"
    if file_content and "\x00" in file_content:
        return "binary_unknown"
    guessed, _ = mimetypes.guess_type(str(candidate))
    if guessed and guessed.startswith("text/"):
        return "document"
    return "binary_unknown"


def directory_analysis_filename(config: dict[str, Any] | None = None) -> str:
    effective = config or load_config()
    directory_analysis = effective.get("directory_analysis", {}) or {}
    return str(directory_analysis.get("filename", "DIRECTORY_ANALYSIS.md") or "DIRECTORY_ANALYSIS.md")


def is_directory_analysis_artifact(path: str | Path, config: dict[str, Any] | None = None) -> bool:
    return Path(path).name == directory_analysis_filename(config)


def is_scannable_file_type(file_type: str) -> bool:
    return file_type in SCANNABLE_FILE_TYPES


def is_review_candidate(
    path: str | Path,
    file_content: str | None = None,
    file_type: str | None = None,
    config: dict[str, Any] | None = None,
) -> bool:
    if is_directory_analysis_artifact(path, config):
        return False
    resolved_type = file_type or categorize_file(path, file_content)
    return is_scannable_file_type(resolved_type)


def load_analysis_text(path: str | Path, file_type: str) -> str:
    if file_type == "image_media":
        return ""
    return read_text_file(path)


def infer_schema_fields(content: str, file_path: str | Path, file_type: str) -> list[str]:
    path = Path(file_path)
    try:
        if file_type == "structured_data" and path.suffix.lower() in {".csv", ".tsv"}:
            delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
            first_line = content.splitlines()[0] if content.splitlines() else ""
            return [field.strip() for field in next(csv.reader([first_line], delimiter=delimiter)) if field.strip()]
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


def extract_data_sources(content: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for match in URL_PATTERN.finditer(content or ""):
        value = match.group(0).rstrip(".,)")
        if value in seen:
            continue
        seen.add(value)
        sources.append({"url_or_path": value, "source_type": "url"})
    for match in PATH_PATTERN.finditer(content or ""):
        value = match.group("path")
        if value in seen:
            continue
        seen.add(value)
        sources.append({"url_or_path": value, "source_type": "local_path"})
    return sources


def identify_sensitive_fields(text: str) -> list[str]:
    lowered = (text or "").lower()
    return [keyword for keyword in SENSITIVE_KEYWORDS if keyword in lowered]


def report_filename_for(file_path: str) -> str:
    stem = Path(file_path).stem
    return f"{slugify_filename(stem)}_analysis_report.md"


def _summarize(file_path: str, file_type: str, content: str, fields: list[str], sources: list[dict[str, str]]) -> str:
    path = Path(file_path)
    if file_type == "source_code":
        lowered = content.lower()
        signals: list[str] = []
        if any(token in lowered for token in ("train", "fit(", "trainer", "epoch")):
            signals.append("model training")
        if any(token in lowered for token in ("predict", "infer", "classify", "score", "recommend")):
            signals.append("automated scoring or inference")
        if any(token in lowered for token in ("scrape", "crawler", "selenium", "beautifulsoup", "playwright")):
            signals.append("data collection")
        if not signals:
            signals.append("application logic")
        return (
            f"{path.name} is {detect_language(file_path) or 'source'} code that appears to implement "
            f"{', '.join(signals)}. It exposes {len(fields)} recognizable fields and {len(sources)} data sources. "
            "This summary is structural context for the LLM review, not the final compliance judgement."
        )
    if file_type == "structured_data":
        return (
            f"{path.name} appears to be structured data with fields such as "
            f"{', '.join(fields[:6]) or 'unknown columns'}. This summary is structural context for the LLM review."
        )
    if file_type == "config":
        return f"{path.name} appears to configure an AI or data-processing workflow."
    if file_type == "document":
        return f"{path.name} is a text document. Sample: {shorten(content, 160)}"
    return f"{path.name} was classified as {file_type.replace('_', ' ')}."


def _predict_output(file_type: str, content: str, fields: list[str]) -> str | None:
    if file_type != "source_code":
        return None
    lowered = content.lower()
    if any(token in lowered for token in ("train", "fit(", "trainer", "epoch")):
        return "This file likely trains or fine-tunes a model artifact for later deployment."
    if any(token in lowered for token in ("predict", "classify", "score", "recommend", "infer")):
        return "This file likely produces predictions, classifications, scores, or recommendations that affect downstream decisions."
    if fields:
        return f"This file transforms records with fields such as {', '.join(fields[:5])} for downstream use."
    return "This file appears to implement logic that transforms inputs into derived outputs."


def analyze_file(
    file_path: str,
    file_type: str | None = None,
    config: dict[str, Any] | None = None,
    query_rag: QueryFn | None = None,
    file_content: str | None = None,
) -> tuple[FileResult, list[dict[str, str]]]:
    effective = config or load_config()
    content = file_content if file_content is not None else ""
    inferred_type = file_type or categorize_file(file_path, content)

    if file_content is None:
        try:
            content = load_analysis_text(file_path, inferred_type)
        except Exception as exc:
            return (
                {
                    "file_path": file_path,
                    "file_type": inferred_type,
                    "language": detect_language(file_path),
                    "status": "ERROR",
                    "summary": "",
                    "predicted_output": None,
                    "findings": [],
                    "report_path": None,
                    "error": str(exc),
                },
                [],
            )

    if content.startswith("<binary file:") or inferred_type in {"image_media", "binary_unknown"}:
        reason = "image/media files are not analysed in v4.0" if inferred_type == "image_media" else "binary file type is not supported"
        return (
            {
                "file_path": file_path,
                "file_type": inferred_type,
                "language": detect_language(file_path),
                "status": "SKIPPED",
                "summary": f"{Path(file_path).name} was skipped because {reason}.",
                "predicted_output": None,
                "findings": [],
                "report_path": None,
                "error": None,
            },
            [],
        )

    if is_directory_analysis_artifact(file_path, effective):
        return (
            {
                "file_path": file_path,
                "file_type": inferred_type,
                "language": detect_language(file_path),
                "status": "SKIPPED",
                "summary": f"{Path(file_path).name} was skipped because it is agent-generated repository context, not source material to review.",
                "predicted_output": None,
                "findings": [],
                "report_path": None,
                "error": None,
            },
            [],
        )

    if not is_scannable_file_type(inferred_type):
        return (
            {
                "file_path": file_path,
                "file_type": inferred_type,
                "language": detect_language(file_path),
                "status": "SKIPPED",
                "summary": (
                    f"{Path(file_path).name} was skipped because only source code, documents, and structured data are reviewed."
                ),
                "predicted_output": None,
                "findings": [],
                "report_path": None,
                "error": None,
            },
            [],
        )

    fields = infer_schema_fields(content, file_path, inferred_type)
    data_sources = extract_data_sources(content)

    result: FileResult = {
        "file_path": file_path,
        "file_type": inferred_type,
        "language": detect_language(file_path),
        "status": "PASS",
        "summary": _summarize(file_path, inferred_type, content, fields, data_sources),
        "predicted_output": _predict_output(inferred_type, content, fields),
        "findings": [],
        "report_path": None,
        "error": None,
    }
    return result, data_sources
