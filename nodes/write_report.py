from __future__ import annotations

from pathlib import Path

from analysis.core import report_filename_for
from analysis.reports import build_file_report_markdown
from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import write_text_file
from utils.compat import traceable


def resolve_workspace_root(file_path: str) -> Path:
    candidate = Path(file_path).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if (parent / ".git").exists() or (parent / "config.yaml").exists() or (parent / "README.md").exists():
            return parent
    return candidate


def resolve_output_dir(file_path: str, config: dict) -> Path:
    root = resolve_workspace_root(file_path)
    return root / config.get("scan", {}).get("output_dir", "compliance-analysis")


@traceable(name="write_report", tags=["compliance-scan", "reporting"])
def write_report_node(state: ComplianceState) -> dict:
    result = state.get("file_result")
    if result is None:
        return {"scan_complete": True}

    output_dir = resolve_output_dir(result["file_path"], state["config"])
    report_path = output_dir / report_filename_for(result["file_path"])
    markdown = build_file_report_markdown(result)
    write_text_file(report_path, markdown, lock_timeout=int(state["config"].get("filesystem", {}).get("write_lock_timeout_s", 30)))

    updated_result = dict(result)
    updated_result["report_path"] = str(report_path)
    event = progress_event(
        "scan_complete",
        file_path=result["file_path"],
        message=f"Report written to {report_path}",
    )
    return {
        "file_result": updated_result,
        "final_report_md": markdown,
        "scan_complete": True,
        "progress_events": [event],
    }
