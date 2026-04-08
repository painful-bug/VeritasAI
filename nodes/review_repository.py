from __future__ import annotations

from pathlib import Path

from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.runnables import RunnableConfig

from analysis.repository_review import ensure_directory_analysis, path_is_within_root, resolve_workspace_root
from models.events import progress_event
from models.state import ComplianceState
from utils.compat import traceable


def _normalize_workspace_root(value: str | None) -> str | None:
    if not value:
        return None
    return str(Path(value).expanduser().resolve())


def _analysis_target_root(state: ComplianceState) -> str | None:
    file_path = state["file_path"]
    workspace_root = _normalize_workspace_root(state.get("opened_workspace_root"))
    restrict_to_workspace = bool(state.get("restrict_directory_analysis_to_workspace", False))

    if workspace_root is not None and path_is_within_root(file_path, workspace_root):
        return workspace_root

    if restrict_to_workspace:
        return None

    return str(resolve_workspace_root(file_path))


@traceable(name="code_reviewer", tags=["compliance-scan", "repository-review"])
def review_repository_node(state: ComplianceState, config: RunnableConfig) -> dict:
    start_event = progress_event(
        "directory_analysis_started",
        file_path=state["file_path"],
        message="Building repository-wide directory analysis context.",
    )
    dispatch_custom_event("progress", start_event, config=config)

    target_root = _analysis_target_root(state)
    if target_root is None:
        skipped_event = progress_event(
            "directory_analysis_skipped",
            file_path=state["file_path"],
            message="Skipped repository context because the file is outside the opened workspace.",
        )
        dispatch_custom_event("progress", skipped_event, config=config)
        return {
            "agentic_context": "",
            "directory_analysis_path": None,
            "workspace_root": state.get("opened_workspace_root"),
            "progress_events": [start_event, skipped_event],
        }

    try:
        analysis = ensure_directory_analysis(target_root, config=state["config"], force=False)
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
