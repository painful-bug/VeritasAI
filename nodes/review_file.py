from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.core import analyze_file, report_filename_for
from analysis.llm_review import assess_file_with_llm
from analysis.reports import build_file_report_markdown
from llm.provider_factory import try_create_llm
from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import write_text_file
from tools.rag_tool import query_rag_tool
from utils.compat import traceable



def _query_rag(description: str, top_k: int, config: dict[str, Any]) -> list[dict[str, Any]]:
    return query_rag_tool(description=description, top_k=top_k, config=config)


@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState) -> dict:
    file_path = state.get("_current_file") or ""
    file_type = state.get("_current_category") or state.get("file_categories", {}).get(file_path, "binary_unknown")
    output_dir = Path(state.get("_analysis_output_dir") or Path(state["target_directory"]) / state["config"].get("scan", {}).get("output_dir", "compliance-analysis"))

    start = progress_event("file_started", file_path=file_path, message=f"Reviewing {Path(file_path).name}")

    try:
        file_result, pending_sources = analyze_file(
            file_path=file_path,
            file_type=file_type,
            config=state["config"],
            query_rag=lambda description, top_k: _query_rag(description, top_k, state["config"]),
        )
        llm = try_create_llm(state["llm_provider"], state["llm_model"], state["config"])
        if llm is not None and file_result["status"] != "ERROR":
            llm_assessment = assess_file_with_llm(
                llm=llm,
                file_path=file_path,
                file_type=file_type,
                base_result=file_result,
                config=state["config"],
                query_rag=lambda description, top_k: _query_rag(description, top_k, state["config"]),
            )
            if llm_assessment:
                file_result["summary"] = llm_assessment["summary"]
                file_result["predicted_output"] = llm_assessment["predicted_output"]
                file_result["status"] = llm_assessment["status"]
                file_result["findings"] = llm_assessment["findings"]
                file_result["notes"] = llm_assessment["notes"]
        report_path = output_dir / report_filename_for(file_path)
        markdown = build_file_report_markdown(file_result)
        write_text_file(report_path, markdown, lock_timeout=int(state["config"].get("filesystem", {}).get("write_lock_timeout_s", 30)))
        file_result["report_path"] = str(report_path)
    except Exception as exc:
        file_result = {
            "file_path": file_path,
            "file_type": file_type,
            "language": None,
            "status": "ERROR",
            "summary": "",
            "predicted_output": None,
            "findings": [],
            "data_sources": [],
            "report_path": None,
            "error": str(exc),
            "notes": ["review_file_node raised an exception"],
        }
        pending_sources = []

    complete = progress_event(
        "file_complete",
        file_path=file_path,
        message=f"Completed {Path(file_path).name} with status {file_result['status']}",
        metadata={"status": file_result["status"], "findings": len(file_result.get("findings", []))},
    )
    return {
        "file_results": [file_result],
        "progress_events": [start, complete],
        "_pending_data_sources": [{**source, "file_path": file_path} for source in pending_sources],
        "_current_file_result": [file_result],
    }
