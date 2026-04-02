from __future__ import annotations

from typing import Any, Callable

from models.state import FileResult, Finding
from utils.strings import extract_tagged_json

QueryFn = Callable[[str, int], list[dict[str, Any]]]

VALID_STATUSES = {"PASS", "WARN", "FAIL", "ERROR", "SKIPPED"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH"}


def _response_text(response: Any) -> str:
    content = getattr(response, "content", response)
    return content if isinstance(content, str) else str(content or "")


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status_from_findings(findings: list[Finding]) -> str:
    severities = {finding["severity"] for finding in findings}
    if "HIGH" in severities:
        return "FAIL"
    if "MEDIUM" in severities:
        return "WARN"
    return "PASS"


def _sanitize_findings(file_path: str, payload: dict[str, Any], rag_hits: list[dict[str, Any]]) -> list[Finding]:
    rag_index = {
        str((hit.get("metadata", {}) or {}).get("chunk_id") or ""): hit.get("metadata", {}) or {}
        for hit in rag_hits
        if isinstance(hit, dict)
    }
    findings: list[Finding] = []
    for raw in payload.get("findings", []):
        if not isinstance(raw, dict):
            continue
        severity = str(raw.get("severity", "LOW")).upper()
        if severity not in VALID_SEVERITIES:
            severity = "LOW"
        rag_chunk_id = str(raw.get("rag_chunk_id") or "")
        rag_page = _int_value(raw.get("rag_page"))
        if rag_chunk_id and rag_chunk_id in rag_index:
            rag_page = _int_value(rag_index[rag_chunk_id].get("page"))
        findings.append(
            {
                "severity": severity,
                "file_path": file_path,
                "start_line": _int_value(raw.get("start_line"), 1),
                "end_line": _int_value(raw.get("end_line"), _int_value(raw.get("start_line"), 1)),
                "regulation_name": str(raw.get("regulation_name") or "Unspecified regulation").strip(),
                "jurisdiction": str(raw.get("jurisdiction") or "Global").strip(),
                "explanation": str(raw.get("explanation") or "").strip(),
                "remedy": str(raw.get("remedy") or "").strip(),
                "rag_chunk_id": rag_chunk_id,
                "rag_page": rag_page,
            }
        )
    return findings


def assess_file_with_llm(
    llm: Any,
    file_path: str,
    file_content: str,
    base_result: FileResult,
    query_rag: QueryFn | None = None,
    top_k: int = 5,
) -> FileResult | None:
    description = base_result["summary"]
    if base_result["findings"]:
        description = " ".join(finding["explanation"] for finding in base_result["findings"][:3])

    rag_hits = query_rag(description, top_k) if query_rag else []
    rag_context = "\n\n".join(
        f"[{index}] chunk_id={hit.get('metadata', {}).get('chunk_id', 'n/a')} "
        f"page={hit.get('metadata', {}).get('page', 'n/a')}\n{hit.get('text', '')}"
        for index, hit in enumerate(rag_hits, start=1)
    )
    prompt = f"""
Review this file for AI ethics compliance.

File path: {file_path}
Baseline status: {base_result['status']}
Baseline summary: {base_result['summary']}
Predicted output: {base_result.get('predicted_output') or 'n/a'}

Knowledge base excerpts:
{rag_context or 'No RAG excerpts available.'}

File content:
```text
{file_content}
```

Return only a FileResult JSON object enclosed in <r>...</r>.
""".strip()

    try:
        response = llm.invoke(prompt)
    except Exception:
        return None

    payload = extract_tagged_json(_response_text(response))
    if not payload:
        return None

    findings = _sanitize_findings(file_path, payload, rag_hits)
    status = str(payload.get("status") or _status_from_findings(findings)).upper()
    if status not in VALID_STATUSES:
        status = _status_from_findings(findings)

    return {
        "file_path": file_path,
        "file_type": str(payload.get("file_type") or base_result["file_type"]),
        "language": payload.get("language") or base_result["language"],
        "status": status,
        "summary": str(payload.get("summary") or base_result["summary"]),
        "predicted_output": payload.get("predicted_output") or base_result["predicted_output"],
        "findings": findings,
        "report_path": None,
        "error": payload.get("error"),
    }
