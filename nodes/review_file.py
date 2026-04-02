from __future__ import annotations

import os
from typing import Any

from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.runnables import RunnableConfig

from analysis.core import analyze_file
from analysis.llm_review import assess_file_with_llm
from graphs.file_review_subgraph import build_file_review_agent
from llm.provider_factory import try_create_llm
from models.events import progress_event
from models.state import ComplianceState, FileResult
from rag.retriever import Retriever
from utils.compat import traceable
from utils.strings import extract_tagged_json


def _rag_query(config: dict[str, Any]):
    retriever = Retriever.get_instance(config)
    return lambda description, top_k: retriever.query(description, top_k=top_k)


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


def _format_reviewed_context(reviewed_context: list[dict[str, Any]]) -> str:
    if not reviewed_context:
        return "No prior reviewed context is available."

    sections: list[str] = []
    for item in reviewed_context[:4]:
        findings = item.get("findings", [])
        finding_lines = []
        for finding in findings[:4]:
            finding_lines.append(
                f"- [{finding.get('severity', 'LOW')}] {finding.get('regulation_name', 'Unspecified regulation')} "
                f"lines {finding.get('start_line', 0)}-{finding.get('end_line', 0)}"
            )
        section_lines = [
            f"Reviewed span: lines {item.get('start_line', 0)}-{item.get('end_line', 0)}",
            f"Summary: {item.get('summary', '')}",
            "Prior findings:",
        ]
        section_lines.extend(finding_lines if finding_lines else ["- None"])
        sections.append("\n".join(section_lines))
    return "\n\n".join(sections)


def _parse_agent_result(raw: Any, fallback: FileResult) -> FileResult | None:
    messages = raw.get("messages") if isinstance(raw, dict) else None
    if not messages:
        return None
    final_message = messages[-1]
    content = getattr(final_message, "content", final_message)
    payload = extract_tagged_json(content if isinstance(content, str) else str(content))
    if not payload:
        return None
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    return {
        "file_path": fallback["file_path"],
        "file_type": str(payload.get("file_type") or fallback["file_type"]),
        "language": payload.get("language") or fallback["language"],
        "status": str(payload.get("status") or fallback["status"]).upper(),
        "summary": str(payload.get("summary") or fallback["summary"]),
        "predicted_output": payload.get("predicted_output") or fallback["predicted_output"],
        "findings": [
            {
                "severity": str(item.get("severity", "LOW")).upper(),
                "file_path": fallback["file_path"],
                "start_line": int(item.get("start_line", 1) or 1),
                "end_line": int(item.get("end_line", item.get("start_line", 1)) or 1),
                "regulation_name": str(item.get("regulation_name") or "Unspecified regulation"),
                "jurisdiction": str(item.get("jurisdiction") or "Global"),
                "explanation": str(item.get("explanation") or ""),
                "remedy": str(item.get("remedy") or ""),
                "rag_chunk_id": str(item.get("rag_chunk_id") or ""),
                "rag_page": int(item.get("rag_page", 0) or 0),
            }
            for item in findings
            if isinstance(item, dict)
        ],
        "report_path": None,
        "error": payload.get("error"),
    }


@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState, config: RunnableConfig) -> dict:
    file_path = state["file_path"]
    file_content = state["file_content"]
    line_offset = int(state.get("line_offset", 0) or 0)
    reviewed_context = state.get("reviewed_context", [])
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

    llm = None
    if state["llm_provider"] not in {"", "deterministic"}:
        llm = try_create_llm(state["llm_provider"], state["llm_model"], config=state["config"])

    if llm is not None and file_result["status"] != "SKIPPED":
        try:
            agent = build_file_review_agent(llm)
            prompt = (
                "Analyse the following file for AI ethics compliance violations.\n"
                f"File path: {file_path}\n"
                f"Baseline assessment: {file_result}\n"
                f"Previously reviewed context:\n{_format_reviewed_context(reviewed_context)}\n\n"
                "Return only a FileResult JSON object in <r>...</r> tags.\n\n"
                f"File content:\n{file_content}"
            )
            agent_result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            parsed = _parse_agent_result(agent_result, file_result)
            if parsed is not None:
                file_result = parsed
        except Exception:
            llm_result = assess_file_with_llm(
                llm=llm,
                file_path=file_path,
                file_content=file_content,
                base_result=file_result,
                query_rag=query_rag,
                top_k=int(state["config"].get("rag", {}).get("top_k", 5)),
            )
            if llm_result is not None:
                file_result = llm_result

    file_result = _apply_line_offset(file_result, line_offset)

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
