from __future__ import annotations

import json
from typing import Any, Callable

from analysis.agentic_runtime import run_pydantic_agentic_review
from models.state import FileResult, Finding
from prompts.loader import load_prompt
from rag.retriever import Retriever
from utils.strings import extract_tagged_json

QueryFn = Callable[[str, int], list[dict[str, Any]]]
WebSearchFn = Callable[[str, int], list[dict[str, Any]]]

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


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return default
    if numeric < 0:
        return 0.0
    if numeric > 1:
        return 1.0
    return numeric


def _bool_value(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if value is None:
        return default
    return bool(value)


def _status_from_findings(findings: list[Finding]) -> str:
    severities = {finding["severity"] for finding in findings}
    if "HIGH" in severities:
        return "FAIL"
    if "MEDIUM" in severities:
        return "WARN"
    return "PASS"


def _agentic_score(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    if key in payload:
        return _float_value(payload.get(key), default)
    return _float_value(payload.get(key.replace(" ", "_")), default)


def _agentic_flag(payload: dict[str, Any], key: str, default: bool = False) -> bool:
    if key in payload:
        return _bool_value(payload.get(key), default)
    return _bool_value(payload.get(key.replace(" ", "_")), default)


def _agentic_text(payload: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        if key in payload and payload.get(key) is not None:
            return str(payload.get(key)).strip()
    return default


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


def _build_retrieval_evidence(hits: list[dict[str, Any]], question: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for hit in hits:
        metadata = hit.get("metadata", {}) or {}
        chunk_id = str(metadata.get("chunk_id") or hit.get("chunk_id") or "")
        page = _int_value(metadata.get("page", hit.get("page", 0)), 0)
        evidence.append(
            {
                "query": str(hit.get("query") or question),
                "chunk_id": chunk_id,
                "page": page,
                "confidence": _float_value(hit.get("confidence"), 0.0),
                "trust_score": _float_value(hit.get("trust_score"), 0.0),
            }
        )
    return evidence


def _build_web_evidence(hits: list[dict[str, Any]], question: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for hit in hits:
        evidence.append(
            {
                "query": question,
                "source": str(hit.get("source") or "web"),
                "title": str(hit.get("title") or hit.get("source") or "web result"),
                "url": str(hit.get("url") or ""),
            }
        )
    return evidence


def _build_review_question(file_path: str, base_result: FileResult) -> str:
    return (
        f"Assess AI ethics compliance risks in file {file_path}. "
        f"Prepared file summary: {base_result['summary']} "
        f"Predicted real-world output: {base_result.get('predicted_output') or 'Unknown'}"
    )


def _compact_reviewed_context(reviewed_context: list[dict[str, Any]] | None) -> str:
    if not reviewed_context:
        return "No nearby reviewed context available."
    compact = []
    for item in reviewed_context[:4]:
        if not isinstance(item, dict):
            continue
        compact.append(
            {
                "start_line": item.get("start_line"),
                "end_line": item.get("end_line"),
                "summary": item.get("summary"),
                "findings": item.get("findings", [])[:6],
            }
        )
    if not compact:
        return "No nearby reviewed context available."
    return json.dumps(compact, ensure_ascii=True)


def _supporting_context(
    *,
    base_result: FileResult,
    reviewed_context: list[dict[str, Any]] | None,
    repository_context: str,
) -> str:
    sections = [f"Prepared file summary:\n{base_result['summary']}"]
    predicted_output = str(base_result.get("predicted_output") or "").strip()
    if predicted_output:
        sections.append(f"Prepared predicted output:\n{predicted_output}")
    if reviewed_context:
        sections.append(f"Nearby reviewed context:\n{_compact_reviewed_context(reviewed_context)}")
    if repository_context.strip():
        sections.append(f"Repository-wide DIRECTORY_ANALYSIS context:\n{repository_context.strip()}")
    return "\n\n".join(sections)


def _needs_web_search(payload: dict[str, Any], thresholds: dict[str, Any]) -> bool:
    if _agentic_flag(payload, "Needs Web Search", default=False):
        return True
    relevancy = _agentic_score(payload, "Relevancy", default=0.0)
    context_quality = _agentic_score(payload, "Context Quality", default=0.0)
    force_relevancy = _float_value(thresholds.get("force_web_search_relevancy_max"), 0.35)
    context_min = _float_value(thresholds.get("context_quality_min"), 0.5)
    return relevancy <= force_relevancy or context_quality < context_min


def _build_prompt(
    *,
    question: str,
    file_path: str,
    file_content: str,
    base_result: FileResult,
    rag_hits: list[dict[str, Any]],
    web_hits: list[dict[str, Any]],
    reviewed_context: list[dict[str, Any]] | None,
    repository_context: str,
) -> str:
    system_prompt = load_prompt("file_reviewer").strip()
    rag_context = "\n\n".join(
        f"[{index}] chunk_id={hit.get('metadata', {}).get('chunk_id', 'n/a')} "
        f"page={hit.get('metadata', {}).get('page', 'n/a')} "
        f"confidence={_float_value(hit.get('confidence'), 0.0):.3f} "
        f"trust={_float_value(hit.get('trust_score'), 0.0):.3f}\n{hit.get('text', '')}"
        for index, hit in enumerate(rag_hits, start=1)
    )
    web_context = "\n\n".join(
        f"[{index}] source={hit.get('source', 'web')} title={hit.get('title', 'n/a')} url={hit.get('url', '')}\n"
        f"{hit.get('content') or hit.get('snippet') or hit.get('body') or ''}"
        for index, hit in enumerate(web_hits, start=1)
    )

    return f"""
SYSTEM INSTRUCTIONS
{system_prompt}

REVIEW TASK
Question: {question}
File path: {file_path}
Prepared file status: {base_result['status']}
Prepared file summary: {base_result['summary']}
Prepared predicted output: {base_result.get('predicted_output')}

Supporting repository and nearby context:
{_supporting_context(base_result=base_result, reviewed_context=reviewed_context, repository_context=repository_context)}

Knowledge base excerpts:
{rag_context or 'No RAG excerpts available.'}

Web search excerpts:
{web_context or 'No web excerpts available.'}

File content:
```text
{file_content}
```
""".strip()


def _llm_error_result(
    *,
    file_path: str,
    base_result: FileResult,
    reason: str,
) -> FileResult:
    result: FileResult = {
        "file_path": file_path,
        "file_type": str(base_result.get("file_type") or "unknown"),
        "language": base_result.get("language"),
        "status": "ERROR",
        "summary": (
            f"LLM compliance review could not be completed for {file_path}. "
            f"Reason: {reason}"
        ),
        "predicted_output": base_result.get("predicted_output"),
        "findings": [],
        "report_path": None,
        "error": reason,
        "agentic_grade": None,
        "retrieval_evidence": [],
        "web_search_evidence": [],
    }
    return result


def _map_payload_to_result(
    *,
    payload: dict[str, Any],
    file_path: str,
    file_content: str,
    base_result: FileResult,
    rag_hits: list[dict[str, Any]],
    web_hits: list[dict[str, Any]],
    question: str,
) -> FileResult:
    del file_content
    findings = _sanitize_findings(file_path, payload, rag_hits)
    if not findings and base_result.get("findings"):
        findings = list(base_result["findings"])

    status = str(payload.get("status") or _status_from_findings(findings)).upper()
    if status not in VALID_STATUSES:
        status = _status_from_findings(findings)

    relevancy = _agentic_score(payload, "Relevancy", default=0.0)
    faithfulness = _agentic_score(payload, "Faithfulness", default=0.0)
    context_quality = _agentic_score(payload, "Context Quality", default=0.0)
    needs_web_search = _agentic_flag(payload, "Needs Web Search", default=False)

    result: FileResult = {
        "file_path": file_path,
        "file_type": str(payload.get("file_type") or base_result["file_type"]),
        "language": payload.get("language") or base_result["language"],
        "status": status,
        "summary": _agentic_text(payload, "summary", default=base_result["summary"]),
        "predicted_output": payload.get("predicted_output") or base_result["predicted_output"],
        "findings": findings,
        "report_path": None,
        "error": payload.get("error"),
        "agentic_grade": {
            "relevancy": relevancy,
            "faithfulness": faithfulness,
            "context_quality": context_quality,
            "needs_web_search": needs_web_search,
            "explanation": _agentic_text(payload, "Explanation", "explanation", default=""),
            "answer": _agentic_text(payload, "Answer", "answer", default=""),
            "retrieval_confidence": max((item.get("confidence", 0.0) for item in rag_hits), default=0.0),
            "trust_level": (
                "high"
                if max((item.get("trust_score", 0.0) for item in rag_hits), default=0.0) >= 0.7
                else "medium"
                if max((item.get("trust_score", 0.0) for item in rag_hits), default=0.0) >= 0.45
                else "low"
            ),
        },
        "retrieval_evidence": _build_retrieval_evidence(rag_hits, question),
        "web_search_evidence": _build_web_evidence(web_hits, question),
    }
    return result


def assess_file_with_llm(
    llm: Any,
    file_path: str,
    file_content: str,
    base_result: FileResult,
    query_rag: QueryFn | None = None,
    top_k: int = 5,
    provider: str = "",
    model: str = "",
    config: dict[str, Any] | None = None,
    web_search_fn: WebSearchFn | None = None,
    reviewed_context: list[dict[str, Any]] | None = None,
    repository_context: str = "",
) -> FileResult:
    effective_config = config or {}
    agentic_config = effective_config.get("agentic", {})
    thresholds = agentic_config.get("grade_thresholds", {}) or {}
    question = _build_review_question(file_path, base_result)
    top_k_effective = int(agentic_config.get("retrieval_top_k", top_k))
    max_retries = int(agentic_config.get("max_retries", 2))
    max_web_results = int(agentic_config.get("web_search_max_results", 3))
    force_web_threshold = _float_value(thresholds.get("force_web_search_relevancy_max"), 0.35)

    rag_hits: list[dict[str, Any]] = query_rag(question, top_k_effective) if query_rag else []
    web_hits: list[dict[str, Any]] = []

    if str(agentic_config.get("runtime_mode", "hybrid")).lower() in {"hybrid", "pydantic"}:
        retriever = Retriever.get_instance(effective_config or None)
        pydantic_result = run_pydantic_agentic_review(
            provider=provider,
            model=model,
            question=question,
            context=_supporting_context(
                base_result=base_result,
                reviewed_context=reviewed_context,
                repository_context=repository_context,
            ),
            retriever=retriever,
            web_search_fn=web_search_fn,
            top_k=top_k_effective,
            max_retries=max_retries,
            max_web_results=max_web_results,
            force_web_threshold=force_web_threshold,
        )
        if pydantic_result is not None:
            payload = pydantic_result.get("payload", {}) or {}
            if isinstance(payload, dict):
                rag_trace = pydantic_result.get("rag_trace", []) or []
                web_trace = pydantic_result.get("web_trace", []) or []
                return _map_payload_to_result(
                    payload=payload,
                    file_path=file_path,
                    file_content=file_content,
                    base_result=base_result,
                    rag_hits=rag_trace,
                    web_hits=web_trace,
                    question=question,
                )

    prompt = _build_prompt(
        question=question,
        file_path=file_path,
        file_content=file_content,
        base_result=base_result,
        rag_hits=rag_hits,
        web_hits=web_hits,
        reviewed_context=reviewed_context,
        repository_context=repository_context,
    )
    try:
        response = llm.invoke(prompt)
    except Exception as exc:
        return _llm_error_result(
            file_path=file_path,
            base_result=base_result,
            reason=f"model invocation failed: {exc}",
        )

    payload = extract_tagged_json(_response_text(response))
    if payload is None:
        return _llm_error_result(
            file_path=file_path,
            base_result=base_result,
            reason="model response did not contain valid <r>...</r> JSON",
        )

    if _needs_web_search(payload, thresholds=thresholds) and web_search_fn is not None:
        try:
            web_hits = web_search_fn(question, max_web_results)
        except Exception:
            web_hits = []
        if web_hits:
            retry_prompt = _build_prompt(
                question=question,
                file_path=file_path,
                file_content=file_content,
                base_result=base_result,
                rag_hits=rag_hits,
                web_hits=web_hits,
                reviewed_context=reviewed_context,
                repository_context=repository_context,
            )
            try:
                retry_response = llm.invoke(retry_prompt)
                retry_payload = extract_tagged_json(_response_text(retry_response))
                if retry_payload is not None:
                    payload = retry_payload
            except Exception as exc:
                return _llm_error_result(
                    file_path=file_path,
                    base_result=base_result,
                    reason=f"model retry after web augmentation failed: {exc}",
                )

    return _map_payload_to_result(
        payload=payload,
        file_path=file_path,
        file_content=file_content,
        base_result=base_result,
        rag_hits=rag_hits,
        web_hits=web_hits,
        question=question,
    )
