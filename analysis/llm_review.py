from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from analysis.core import detect_language, load_analysis_text
from models.state import FileResult, Finding
from utils.strings import extract_tagged_json, shorten

QueryFn = Callable[[str, int], list[dict[str, Any]]]

VALID_STATUSES = {"PASS", "WARN", "FAIL"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH"}
STATUS_ORDER = {"PASS": 0, "WARN": 1, "FAIL": 2}


def _response_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    return str(content or "")


def _invoke_json(llm: Any, prompt: str) -> dict[str, Any] | None:
    try:
        response = llm.invoke(prompt)
    except Exception:
        return None
    return extract_tagged_json(_response_text(response))


def _status_from_findings(findings: list[Finding]) -> str:
    severities = {finding["severity"] for finding in findings}
    if "HIGH" in severities:
        return "FAIL"
    if "MEDIUM" in severities:
        return "WARN"
    return "PASS"


def _as_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


def _line_numbered_text(text: str) -> str:
    return "\n".join(f"{index}: {line}" for index, line in enumerate(text.splitlines(), start=1))


def _chunk_text_by_lines(text: str, max_chars: int = 12000, overlap_lines: int = 20) -> list[dict[str, Any]]:
    lines = text.splitlines()
    if not lines:
        return [{"start_line": 1, "end_line": 1, "text": ""}]

    chunks: list[dict[str, Any]] = []
    start = 0
    total_lines = len(lines)
    while start < total_lines:
        current: list[str] = []
        char_count = 0
        end = start
        while end < total_lines:
            candidate = lines[end]
            candidate_len = len(candidate) + 1
            if current and char_count + candidate_len > max_chars:
                break
            current.append(candidate)
            char_count += candidate_len
            end += 1
        if not current:
            current.append(lines[end])
            end += 1
        chunks.append({"start_line": start + 1, "end_line": end, "text": "\n".join(current)})
        if end >= total_lines:
            break
        next_start = max(end - overlap_lines, start + 1)
        start = next_start
    return chunks


def _summarize_large_file(llm: Any, file_path: str, file_type: str, content: str, max_inline_chars: int) -> tuple[str, list[str]]:
    if len(content) <= max_inline_chars:
        return _line_numbered_text(content), []

    chunk_summaries: list[str] = []
    notes: list[str] = []
    for index, chunk in enumerate(_chunk_text_by_lines(content), start=1):
        prompt = f"""
TASK: CHUNK_SUMMARY
You are reviewing one chunk of a file for AI-act and AI-rules compliance analysis.
File: {file_path}
File type: {file_type}
Chunk number: {index}
Chunk line range: {chunk['start_line']}-{chunk['end_line']}

Summarize only facts visible in this chunk that matter for AI compliance review.
Focus on:
- what this chunk does or describes
- any AI/ML, automated decision, surveillance, biometric, profiling, generative, safety, or governance signals
- any sensitive or protected attributes
- any dataset, model, or external service references
- any missing oversight, review, audit, or disclosure controls if clearly visible

Return only:
<RESULT>{{
  "summary": "...",
  "compliance_signals": ["..."],
  "potential_concerns": ["..."],
  "data_sources": ["..."],
  "sensitive_fields": ["..."]
}}</RESULT>

Chunk content:
```text
{_line_numbered_text(chunk['text'])}
```
""".strip()
        payload = _invoke_json(llm, prompt)
        if not payload:
            chunk_summaries.append(
                f"Chunk {index} lines {chunk['start_line']}-{chunk['end_line']}: {shorten(chunk['text'], 400)}"
            )
            notes.append(f"Chunk {index} used fallback summarization because the LLM did not return structured JSON.")
            continue

        summary = str(payload.get("summary") or "No compliance-relevant facts extracted.").strip()
        signals = [str(item).strip() for item in payload.get("compliance_signals", []) if str(item).strip()]
        concerns = [str(item).strip() for item in payload.get("potential_concerns", []) if str(item).strip()]
        data_sources = [str(item).strip() for item in payload.get("data_sources", []) if str(item).strip()]
        sensitive_fields = [str(item).strip() for item in payload.get("sensitive_fields", []) if str(item).strip()]

        rendered = [f"Chunk {index} lines {chunk['start_line']}-{chunk['end_line']}: {summary}"]
        if signals:
            rendered.append(f"Signals: {', '.join(signals[:6])}")
        if concerns:
            rendered.append(f"Concerns: {', '.join(concerns[:6])}")
        if data_sources:
            rendered.append(f"Data sources: {', '.join(data_sources[:6])}")
        if sensitive_fields:
            rendered.append(f"Sensitive fields: {', '.join(sensitive_fields[:8])}")
        chunk_summaries.append(" | ".join(rendered))

    notes.append(f"Large file review used {len(chunk_summaries)} chunk summaries covering the full file content.")
    return "\n".join(chunk_summaries), notes


def _generate_rag_queries(
    llm: Any,
    file_path: str,
    file_type: str,
    summary: str,
    predicted_output: str | None,
    reasoning_basis: str,
    top_k: int,
) -> tuple[list[str], list[str]]:
    prompt = f"""
TASK: RAG_QUERY_GENERATION
Generate up to {top_k} precise search queries for retrieving AI laws, AI acts, AI governance rules, or regulatory obligations relevant to this file.

Rules:
- Base the queries only on the file evidence provided.
- Queries must be specific enough to retrieve applicable rules, not generic AI ethics commentary.
- If the file does not appear to implement, configure, document, or process any AI-related or automated decision workflow, return an empty list.
- Prefer queries tied to concrete use cases such as hiring, credit, biometrics, surveillance, profiling, generative AI, children, sensitive personal data, or high-risk AI documentation duties.

Return only:
<RESULT>{{
  "queries": ["..."],
  "notes": ["..."]
}}</RESULT>

File: {file_path}
Type: {file_type}
Baseline summary: {summary}
Predicted output: {predicted_output or 'n/a'}

Review basis:
{reasoning_basis}
""".strip()
    payload = _invoke_json(llm, prompt)
    if not payload:
        return [], ["The LLM did not return structured RAG queries; falling back to deterministic review."]

    queries = []
    for value in payload.get("queries", []):
        query = " ".join(str(value).split())
        if query and query not in queries:
            queries.append(query)
        if len(queries) >= top_k:
            break
    notes = [str(item).strip() for item in payload.get("notes", []) if str(item).strip()]
    return queries, notes


def _retrieve_rag_hits(queries: list[str], query_rag: QueryFn, top_k: int) -> tuple[list[dict[str, Any]], list[str]]:
    seen: set[tuple[str, int | None]] = set()
    unique_hits: list[dict[str, Any]] = []
    notes: list[str] = []
    for query in queries:
        hits = query_rag(query, top_k)
        notes.append(f"RAG query: {query} -> {len(hits)} hits")
        for hit in hits:
            metadata = hit.get("metadata", {}) if isinstance(hit, dict) else {}
            key = (str(metadata.get("chunk_id") or ""), _as_int(metadata.get("page")))
            if key in seen:
                continue
            seen.add(key)
            unique_hits.append(hit)
    return unique_hits, notes


def _render_rag_hits(rag_hits: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for index, hit in enumerate(rag_hits, start=1):
        metadata = hit.get("metadata", {}) if isinstance(hit, dict) else {}
        rendered.append(
            f"[{index}] chunk_id={metadata.get('chunk_id', 'n/a')} page={metadata.get('page', 'n/a')}\n"
            f"Excerpt: {shorten(str(hit.get('text', '')), 700)}"
        )
    return "\n\n".join(rendered)


def _validate_findings(payload: dict[str, Any], file_path: str, rag_hits: list[dict[str, Any]]) -> list[Finding]:
    rag_by_chunk = {
        str((hit.get("metadata", {}) or {}).get("chunk_id") or ""): (hit.get("metadata", {}) or {})
        for hit in rag_hits
        if isinstance(hit, dict)
    }
    findings: list[Finding] = []
    for index, raw in enumerate(payload.get("findings", []), start=1):
        if not isinstance(raw, dict):
            continue
        severity = str(raw.get("severity", "LOW")).upper()
        if severity not in VALID_SEVERITIES:
            severity = "LOW"
        rag_chunk_id = str(raw.get("rag_chunk_id") or "").strip() or None
        rag_page = _as_int(raw.get("rag_page"))
        if rag_chunk_id and rag_chunk_id in rag_by_chunk:
            rag_page = _as_int(rag_by_chunk[rag_chunk_id].get("page"))
        findings.append(
            {
                "id": f"F{index:03d}",
                "title": str(raw.get("title") or f"Compliance finding {index}").strip(),
                "severity": severity,
                "file_path": file_path,
                "start_line": _as_int(raw.get("start_line")),
                "end_line": _as_int(raw.get("end_line")),
                "section_desc": str(raw.get("section_desc") or "File-level assessment").strip(),
                "regulations": [str(item).strip() for item in raw.get("regulations", []) if str(item).strip()],
                "jurisdictions": [str(item).strip() for item in raw.get("jurisdictions", []) if str(item).strip()],
                "explanation": str(raw.get("explanation") or "").strip(),
                "rag_chunk_id": rag_chunk_id,
                "rag_page": rag_page,
            }
        )
    return findings


def assess_file_with_llm(
    llm: Any,
    file_path: str,
    file_type: str,
    base_result: FileResult,
    config: dict[str, Any],
    query_rag: QueryFn,
) -> dict[str, Any] | None:
    if file_type in {"image_media", "binary_unknown"}:
        return None

    review_config = config.get("review", {})
    max_inline_chars = int(review_config.get("llm_inline_content_chars", 30000))
    rag_query_count = int(review_config.get("llm_rag_query_count", 5))
    rag_hits_per_query = int(review_config.get("llm_rag_hits_per_query", 3))

    content = load_analysis_text(file_path, file_type, max_chars=None)
    if not content:
        return None

    reasoning_basis, notes = _summarize_large_file(llm, file_path, file_type, content, max_inline_chars=max_inline_chars)
    query_notes: list[str] = []
    queries, generated_notes = _generate_rag_queries(
        llm=llm,
        file_path=file_path,
        file_type=file_type,
        summary=base_result.get("summary") or "",
        predicted_output=base_result.get("predicted_output"),
        reasoning_basis=reasoning_basis,
        top_k=rag_query_count,
    )
    query_notes.extend(generated_notes)
    if not queries:
        return {
            "summary": base_result.get("summary") or "",
            "predicted_output": base_result.get("predicted_output"),
            "status": "PASS",
            "findings": [],
            "notes": list(
                dict.fromkeys(
                    list(base_result.get("notes", []))
                    + notes
                    + query_notes
                    + ["LLM review found no AI-regulatory issue requiring RAG retrieval; file marked PASS."]
                )
            ),
        }

    rag_hits, retrieval_notes = _retrieve_rag_hits(queries, query_rag, rag_hits_per_query)
    query_notes.extend(retrieval_notes)
    if not rag_hits:
        return {
            "summary": base_result.get("summary") or "",
            "predicted_output": base_result.get("predicted_output"),
            "status": "PASS",
            "findings": [],
            "notes": list(
                dict.fromkeys(
                    list(base_result.get("notes", []))
                    + notes
                    + query_notes
                    + ["LLM review retrieved no relevant RAG excerpts establishing a rule violation; file marked PASS."]
                )
            ),
        }

    assessment_prompt = f"""
TASK: FINAL_FILE_ASSESSMENT
You are deciding whether a single file complies with AI acts, AI laws, and related regulatory rules.

Decision rules:
- Read the file evidence provided below. This evidence covers the full file content either directly or through chunk summaries.
- Use the retrieved RAG excerpts as the legal and regulatory grounding for any finding.
- A file is PASS if no retrieved rule or act is actually violated by the file content.
- Do not create findings for vague future misuse. Findings must be tied to what the file actually does, configures, stores, documents, or enables.
- If there are only minor governance concerns with no actual rule violation, you may create LOW-severity findings while still leaving the overall status as PASS.
- If there are no supported findings, return an empty findings list and status PASS.
- Every finding must cite one of the provided RAG excerpts using its chunk_id and page.

Return only:
<RESULT>{{
  "summary": "...",
  "predicted_output": "...",
  "status": "PASS|WARN|FAIL",
  "notes": ["..."],
  "findings": [
    {{
      "title": "...",
      "severity": "LOW|MEDIUM|HIGH",
      "start_line": 1,
      "end_line": 3,
      "section_desc": "Lines 1-3",
      "regulations": ["..."],
      "jurisdictions": ["..."],
      "explanation": "...",
      "rag_chunk_id": "...",
      "rag_page": 1
    }}
  ]
}}</RESULT>

File path: {file_path}
File type: {file_type}
Language: {detect_language(file_path) or 'n/a'}
Baseline summary: {base_result.get('summary') or 'n/a'}
Baseline predicted output: {base_result.get('predicted_output') or 'n/a'}
Detected data sources: {', '.join(source['url_or_path'] for source in base_result.get('data_sources', [])) or 'None'}

File evidence:
{reasoning_basis}

Retrieved regulation excerpts:
{_render_rag_hits(rag_hits)}
""".strip()
    payload = _invoke_json(llm, assessment_prompt)
    if not payload:
        return None

    findings = _validate_findings(payload, file_path, rag_hits)
    derived_status = _status_from_findings(findings)
    requested_status = str(payload.get("status", derived_status)).upper()
    if requested_status not in VALID_STATUSES:
        requested_status = derived_status
    if STATUS_ORDER[requested_status] < STATUS_ORDER[derived_status]:
        requested_status = derived_status

    combined_notes = list(dict.fromkeys(
        list(base_result.get("notes", []))
        + notes
        + query_notes
        + [str(item).strip() for item in payload.get("notes", []) if str(item).strip()]
        + ["Final compliance status was determined by LLM review grounded in retrieved RAG excerpts."]
    ))

    return {
        "summary": str(payload.get("summary") or base_result.get("summary") or "").strip(),
        "predicted_output": str(payload.get("predicted_output") or base_result.get("predicted_output") or "").strip() or None,
        "status": requested_status,
        "findings": findings,
        "notes": combined_notes,
    }
