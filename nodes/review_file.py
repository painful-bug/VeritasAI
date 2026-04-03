from __future__ import annotations

import os
from typing import Any

from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.runnables import RunnableConfig

from analysis.core import analyze_file
from analysis.llm_review import assess_file_with_llm
from llm.provider_factory import try_create_llm
from models.events import progress_event
from models.state import ComplianceState, FileResult
from rag.retriever import Retriever
from tools.web_search_tool import web_search_tool
from utils.compat import traceable


def _rag_query(config: dict[str, Any]):
    retriever = Retriever.get_instance(config)
    return lambda description, top_k: retriever.query_for_compliance(description, top_k=top_k)


def _apply_line_offset(file_result: FileResult, line_offset: int) -> FileResult:
    if line_offset <= 0:
        return file_result

    updated = dict(file_result)
    updated["findings"] = [
        {
            **finding,
            "start_line": max(1, int(finding["start_line"]) + line_offset),
            "end_line": max(1, int(finding["end_line"]) + line_offset),
        }
        for finding in file_result.get("findings", [])
    ]
    return updated


def _llm_required_error(
    base_result: FileResult,
    *,
    provider: str,
    model: str,
    reason: str,
) -> FileResult:
    result = dict(base_result)
    result["status"] = "ERROR"
    result["summary"] = (
        f"LLM compliance review could not be completed for {os.path.basename(base_result['file_path'])}. "
        f"Reason: {reason}"
    )
    result["findings"] = []
    result["error"] = (
        f"provider={provider or 'unknown'} model={model or 'unknown'}: {reason}"
    )
    result["agentic_grade"] = None
    result["retrieval_evidence"] = []
    result["web_search_evidence"] = []
    return result


@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState, config: RunnableConfig) -> dict:
    file_path = state["file_path"]
    file_content = state["file_content"]
    line_offset = int(state.get("line_offset", 0) or 0)
    query_rag = _rag_query(state["config"])

    start_event = progress_event(
        "file_started",
        file_path=file_path,
        message=f"Reviewing: {os.path.basename(file_path)}",
    )
    dispatch_custom_event("progress", start_event, config=config)

    file_result, _ = analyze_file(
        file_path=file_path,
        config=state["config"],
        query_rag=query_rag,
        file_content=file_content,
    )

    llm_enabled = bool(state.get("config", {}).get("agentic", {}).get("enabled", True))

    if file_result["status"] not in {"SKIPPED", "ERROR"}:
        if not llm_enabled:
            file_result = _llm_required_error(
                file_result,
                provider=state.get("llm_provider", ""),
                model=state.get("llm_model", ""),
                reason="LLM review is disabled in config",
            )
        else:
            llm = try_create_llm(state["llm_provider"], state["llm_model"], config=state["config"])
            if llm is None:
                file_result = _llm_required_error(
                    file_result,
                    provider=state.get("llm_provider", ""),
                    model=state.get("llm_model", ""),
                    reason="LLM client could not be created",
                )
            else:
                file_result = assess_file_with_llm(
                    llm=llm,
                    file_path=file_path,
                    file_content=file_content,
                    base_result=file_result,
                    query_rag=query_rag,
                    top_k=int(state["config"].get("rag", {}).get("top_k", 3)),
                    provider=state.get("llm_provider", ""),
                    model=state.get("llm_model", ""),
                    config=state.get("config", {}),
                    web_search_fn=web_search_tool,
                    reviewed_context=state.get("reviewed_context", []),
                    repository_context=state.get("agentic_context", ""),
                )

    file_result = _apply_line_offset(file_result, line_offset)

    agentic_grade = file_result.get("agentic_grade") if isinstance(file_result, dict) else None
    if isinstance(agentic_grade, dict):
        dispatch_custom_event("agentic_grade", agentic_grade, config=config)
    web_evidence = file_result.get("web_search_evidence") if isinstance(file_result, dict) else None
    if isinstance(web_evidence, list) and web_evidence:
        dispatch_custom_event(
            "agentic_web_search",
            {
                "count": len(web_evidence),
                "sources": [item.get("source", "web") for item in web_evidence[:5] if isinstance(item, dict)],
            },
            config=config,
        )
    retrieval_evidence = file_result.get("retrieval_evidence") if isinstance(file_result, dict) else None
    if isinstance(retrieval_evidence, list) and retrieval_evidence:
        dispatch_custom_event(
            "agentic_retrieval",
            {
                "count": len(retrieval_evidence),
                "top_trust": max(
                    (
                        float(item.get("trust_score", 0.0))
                        for item in retrieval_evidence
                        if isinstance(item, dict)
                    ),
                    default=0.0,
                ),
            },
            config=config,
        )

    for finding in file_result.get("findings", []):
        dispatch_custom_event("violation_found", finding, config=config)

    complete_event = progress_event(
        "file_complete",
        file_path=file_path,
        message=f"Completed: {os.path.basename(file_path)} → {file_result['status']} ({len(file_result['findings'])} findings)",
    )
    dispatch_custom_event("progress", complete_event, config=config)

    return {
        "file_result": file_result,
        "progress_events": [start_event, complete_event],
    }
