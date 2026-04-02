from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.core import merge_data_source_results, validate_data_source_reference
from analysis.reports import build_file_report_markdown
from graphs.data_validator_subgraph import build_data_validator_agent
from llm.provider_factory import try_create_llm
from models.events import progress_event
from models.state import ComplianceState, DataSourceResult
from tools.filesystem_tools import write_text_file
from tools.rag_tool import query_rag_tool
from tools.web_search_tool import web_search_tool
from utils.compat import traceable
from utils.strings import extract_tagged_json



def _query_rag(description: str, top_k: int, config: dict[str, Any]) -> list[dict[str, Any]]:
    return query_rag_tool(description=description, top_k=top_k, config=config)



def _maybe_agent_override(state: ComplianceState, source: dict[str, Any], deterministic: DataSourceResult) -> DataSourceResult:
    llm = try_create_llm(state["llm_provider"], state["llm_model"], state["config"])
    if llm is None:
        return deterministic

    agent = build_data_validator_agent(llm)
    if agent is None:
        return deterministic

    prompt = f"""
You are validating a data source reference.
Source: {source.get('url_or_path')}
Source type: {source.get('source_type')}
Deterministic result: {deterministic}
Return only <RESULT>{{"verdict": "PASS|WARN|FAIL|UNKNOWN", "description": "...", "concerns": ["..."], "regulations": ["..."]}}</RESULT>.
Do not add fields that are not present in the schema.
""".strip()
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    except Exception:
        return deterministic

    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return deterministic
    payload = extract_tagged_json(getattr(messages[-1], "content", str(messages[-1])) or "")
    if not payload:
        return deterministic

    merged = dict(deterministic)
    if payload.get("verdict") in {"PASS", "WARN", "FAIL", "UNKNOWN"}:
        merged["verdict"] = payload["verdict"]
    if isinstance(payload.get("description"), str) and payload["description"].strip():
        merged["description"] = payload["description"].strip()
    if isinstance(payload.get("concerns"), list):
        merged["concerns"] = [str(item) for item in payload["concerns"]]
    if isinstance(payload.get("regulations"), list):
        merged["regulations"] = [str(item) for item in payload["regulations"]]
    return merged


@traceable(name="validate_data_source", tags=["compliance-scan", "data-validation"])
def validate_data_source_node(state: ComplianceState) -> dict:
    pending_sources = state.get("_pending_data_sources", [])
    current_results = state.get("_current_file_result", [])
    if not pending_sources or not current_results:
        return {"progress_events": []}

    results_by_file = {result["file_path"]: result for result in current_results}
    validated_by_file: dict[str, list[DataSourceResult]] = {}
    events = []
    for source in pending_sources:
        file_path = source.get("file_path", "")
        current_result = dict(results_by_file.get(file_path, {}))
        if not current_result:
            continue
        events.append(
            progress_event(
                "data_source_found",
                file_path=file_path,
                message=f"Validating {source.get('url_or_path')}",
            )
        )
        deterministic = validate_data_source_reference(
            source=source,
            current_file=file_path,
            target_directory=state["target_directory"],
            config=state["config"],
            query_rag=lambda description, top_k: _query_rag(description, top_k, state["config"]),
            web_search=lambda query, max_results: web_search_tool(query=query, max_results=max_results),
        )
        validated_by_file.setdefault(file_path, []).append(_maybe_agent_override(state, source, deterministic))

    merged_results = []
    for file_path, validated in validated_by_file.items():
        merged_result = merge_data_source_results(results_by_file[file_path], validated)
        if merged_result.get("report_path"):
            write_text_file(
                merged_result["report_path"],
                build_file_report_markdown(merged_result),
                lock_timeout=int(state["config"].get("filesystem", {}).get("write_lock_timeout_s", 30)),
            )
        merged_results.append(merged_result)
        events.append(
            progress_event(
                "data_source_validated",
                file_path=file_path,
                message=f"Validated {len(validated)} data sources",
                metadata={"count": len(validated)},
            )
        )

    return {
        "file_results": merged_results,
        "progress_events": events,
    }
