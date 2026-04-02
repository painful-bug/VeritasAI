from __future__ import annotations

from models.events import progress_event
from models.state import ComplianceState
from utils.compat import traceable

STATUS_SCORE = {"FAIL": 4, "WARN": 3, "PASS": 2, "SKIPPED": 1, "ERROR": 0}


def _result_quality(result: dict) -> tuple[int, int, int, int, int]:
    validated_sources = sum(1 for source in result.get("data_sources", []) if source.get("verdict") != "PENDING")
    return (
        STATUS_SCORE.get(result.get("status", "ERROR"), 0),
        1 if not result.get("error") else 0,
        len(result.get("findings", [])),
        validated_sources,
        1 if result.get("report_path") else 0,
    )


@traceable(name="join_results", tags=["compliance-scan", "aggregation"])
def join_results_node(state: ComplianceState) -> dict:
    deduped = {}
    for result in state.get("file_results", []):
        current = deduped.get(result["file_path"])
        if current is None or _result_quality(result) > _result_quality(current):
            deduped[result["file_path"]] = result
    return {
        "_deduped_file_results": list(deduped.values()),
        "progress_events": [
            progress_event(
                "aggregation_complete",
                message=f"Aggregated {len(deduped)} file results.",
                metadata={"files": len(deduped)},
            )
        ],
    }
