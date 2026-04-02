from __future__ import annotations

from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import safe_mkdir
from utils.compat import traceable

from .write_report import resolve_output_dir


@traceable(name="initialize", tags=["compliance-scan", "setup"])
def initialize_node(state: ComplianceState) -> dict:
    output_dir = resolve_output_dir(state["file_path"], state["config"])
    safe_mkdir(output_dir)
    return {
        "progress_events": [
            progress_event(
                "scan_started",
                file_path=state["file_path"],
                message=f"Scan initialised for: {state['file_path']}",
            )
        ]
    }
