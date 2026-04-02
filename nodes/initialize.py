from __future__ import annotations

from pathlib import Path

from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import safe_mkdir
from utils.compat import traceable


@traceable(name="initialize", tags=["compliance-scan", "setup"])
def initialize_node(state: ComplianceState) -> dict:
    target_directory = Path(state["target_directory"]).expanduser().resolve()
    if not target_directory.exists() or not target_directory.is_dir():
        return {"scan_error": f"Target directory does not exist: {target_directory}"}

    output_dir = target_directory / state["config"].get("scan", {}).get("output_dir", "compliance-analysis")
    safe_mkdir(output_dir)
    return {
        "all_files": [],
        "skipped_files": [],
        "file_categories": {},
        "scan_complete": False,
        "scan_error": None,
        "_analysis_output_dir": str(output_dir),
        "progress_events": [
            progress_event(
                "scan_started",
                message=f"Scan initialised for {target_directory}",
                metadata={"output_dir": str(output_dir)},
            )
        ],
    }
