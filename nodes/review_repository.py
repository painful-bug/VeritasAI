from __future__ import annotations

from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.runnables import RunnableConfig

from analysis.repository_review import ensure_directory_analysis
from models.events import progress_event
from models.state import ComplianceState
from utils.compat import traceable


@traceable(name="code_reviewer", tags=["compliance-scan", "repository-review"])
def review_repository_node(state: ComplianceState, config: RunnableConfig) -> dict:
    start_event = progress_event(
        "directory_analysis_started",
        file_path=state["file_path"],
        message="Building repository-wide directory analysis context.",
    )
    dispatch_custom_event("progress", start_event, config=config)

    try:
        analysis = ensure_directory_analysis(state["file_path"], config=state["config"], force=False)
    except Exception as exc:
        error_event = progress_event(
            "directory_analysis_failed",
            file_path=state["file_path"],
            message=f"Directory analysis failed: {exc}",
        )
        dispatch_custom_event("progress", error_event, config=config)
        return {
            "agentic_context": "",
            "directory_analysis_path": None,
            "workspace_root": None,
            "progress_events": [start_event, error_event],
        }

    payload = {
        "path": analysis["analysis_path"],
        "updated": analysis["updated"],
        "file_count": analysis["file_count"],
        "directory_count": analysis["directory_count"],
    }
    dispatch_custom_event("directory_analysis_ready", payload, config=config)
    complete_event = progress_event(
        "directory_analysis_ready",
        file_path=state["file_path"],
        message=(
            f"Repository analysis {'updated' if analysis['updated'] else 'loaded'} "
            f"from {analysis['analysis_path']}"
        ),
        **payload,
    )
    dispatch_custom_event("progress", complete_event, config=config)
    return {
        "agentic_context": analysis["content"],
        "directory_analysis_path": analysis["analysis_path"],
        "workspace_root": analysis["workspace_root"],
        "progress_events": [start_event, complete_event],
    }
