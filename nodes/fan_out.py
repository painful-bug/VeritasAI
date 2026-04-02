from __future__ import annotations

from pathlib import Path

from analysis.core import categorize_file
from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import list_directory_robust
from utils.compat import traceable


@traceable(name="fan_out_files", tags=["compliance-scan", "discovery"])
def fan_out_files_node(state: ComplianceState) -> dict:
    config = state["config"]
    scan_config = config.get("scan", {})
    excluded_dirs = set(scan_config.get("excluded_dirs", []))
    excluded_extensions = {extension.lower() for extension in scan_config.get("excluded_extensions", [])}
    max_size_bytes = int(scan_config.get("max_file_size_mb", 10) * 1024 * 1024)
    output_dir_name = scan_config.get("output_dir", "compliance-analysis")

    discovered = list_directory_robust(state["target_directory"], recursive=True, excluded_dirs=excluded_dirs)

    accepted: list[str] = []
    skipped: list[str] = []
    categories: dict[str, str] = {}
    for entry in discovered:
        path = Path(str(entry["path"]))
        if output_dir_name in path.parts:
            skipped.append(str(path))
            continue
        if path.suffix.lower() in excluded_extensions or int(entry["size_bytes"]) > max_size_bytes:
            skipped.append(str(path))
            continue
        category = categorize_file(path)
        accepted.append(str(path))
        categories[str(path)] = category

    return {
        "all_files": accepted,
        "skipped_files": skipped,
        "file_categories": categories,
        "progress_events": [
            progress_event(
                "discovery_complete",
                message=f"Discovered {len(accepted)} files to scan and skipped {len(skipped)} files.",
                metadata={"accepted": len(accepted), "skipped": len(skipped)},
            )
        ],
    }
