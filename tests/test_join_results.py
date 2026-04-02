from __future__ import annotations

from nodes.join_results import join_results_node


def test_join_results_prefers_richer_duplicate_result() -> None:
    error_result = {
        "file_path": "/tmp/demo.py",
        "file_type": "source_code",
        "language": "Python",
        "status": "ERROR",
        "summary": "",
        "predicted_output": None,
        "findings": [],
        "data_sources": [],
        "report_path": None,
        "error": "transient failure",
        "notes": [],
    }
    merged_result = {
        "file_path": "/tmp/demo.py",
        "file_type": "source_code",
        "language": "Python",
        "status": "FAIL",
        "summary": "unsafe file",
        "predicted_output": "produces a harmful decision",
        "findings": [{"id": "F001", "severity": "HIGH"}],
        "data_sources": [{"url_or_path": "./data.csv", "verdict": "WARN"}],
        "report_path": "/tmp/demo_report.md",
        "error": None,
        "notes": [],
    }

    state = {"file_results": [error_result, merged_result]}
    result = join_results_node(state)

    assert result["_deduped_file_results"][0]["status"] == "FAIL"
    assert result["_deduped_file_results"][0]["error"] is None
    assert len(result["_deduped_file_results"][0]["findings"]) == 1
