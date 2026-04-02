from __future__ import annotations

import asyncio
import json
from pathlib import Path

from graphs.compliance_graph import compile_graph


def test_graph_streams_violation_events_and_writes_report(tmp_path: Path) -> None:
    file_path = tmp_path / "unsafe_hiring.py"
    file_path.write_text(
        """
features = ["gender", "age"]
model.fit(X, y)
# hiring decision
""".strip(),
        encoding="utf-8",
    )

    graph = compile_graph(checkpointer=False, config={"checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")}})
    initial_state = {
        "file_path": str(file_path),
        "file_content": file_path.read_text(encoding="utf-8"),
        "llm_provider": "deterministic",
        "llm_model": "deterministic",
        "config": {
            "scan": {"output_dir": "compliance-analysis"},
            "rag": {"top_k": 1},
            "filesystem": {"write_lock_timeout_s": 5},
            "checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")},
        },
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }

    async def collect_events():
        return [
            event
            async for event in graph.astream_events(
                initial_state,
                config={"configurable": {"thread_id": "graph-test"}},
                version="v2",
            )
        ]

    events = asyncio.run(collect_events())

    assert any(event["event"] == "on_custom_event" and event["name"] == "violation_found" for event in events)
    write_report_end = next(
        event for event in events if event["event"] == "on_chain_end" and event["name"] == "write_report"
    )
    output = write_report_end["data"]["output"]
    assert output["scan_complete"] is True
    assert output["file_result"]["report_path"]
    assert Path(output["file_result"]["report_path"]).exists()
    json.dumps(output["file_result"])


def test_graph_applies_line_offset_to_incremental_snippets(tmp_path: Path) -> None:
    file_path = tmp_path / "incremental_unsafe_hiring.py"
    file_path.write_text(
        """
features = ["gender", "age"]
model.fit(X, y)
""".strip(),
        encoding="utf-8",
    )

    graph = compile_graph(checkpointer=False, config={"checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")}})
    initial_state = {
        "file_path": str(file_path),
        "file_content": 'features = ["gender", "age"]\nmodel.fit(X, y)',
        "llm_provider": "deterministic",
        "llm_model": "deterministic",
        "line_offset": 9,
        "config": {
            "scan": {"output_dir": "compliance-analysis"},
            "rag": {"top_k": 1},
            "filesystem": {"write_lock_timeout_s": 5},
            "checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")},
        },
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }

    result = graph.invoke(initial_state, config={"configurable": {"thread_id": "graph-offset-test"}})
    findings = result["file_result"]["findings"]

    assert findings
    assert min(finding["start_line"] for finding in findings) >= 10
