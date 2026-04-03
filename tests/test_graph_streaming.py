from __future__ import annotations

import asyncio
import json
from pathlib import Path

from graphs.compliance_graph import compile_graph
import nodes.review_file as review_file_module


def _stub_llm_review(monkeypatch) -> None:
    monkeypatch.setattr(review_file_module, "try_create_llm", lambda provider, model, config=None: object())

    def fake_assess_file_with_llm(**kwargs):
        file_path = kwargs["file_path"]
        return {
            "file_path": file_path,
            "file_type": "source_code",
            "language": "Python",
            "status": "FAIL",
            "summary": "LLM found a high-risk employment AI issue.",
            "predicted_output": "Produces hiring recommendations.",
            "findings": [
                {
                    "severity": "HIGH",
                    "file_path": file_path,
                    "start_line": 1,
                    "end_line": 1,
                    "regulation_name": "EU AI Act — Article 10 Data and Data Governance",
                    "jurisdiction": "EU",
                    "explanation": "Protected attributes appear in an employment-related model flow.",
                    "remedy": "Remove protected attributes and add documented oversight controls.",
                    "rag_chunk_id": "p1_c0",
                    "rag_page": 1,
                }
            ],
            "report_path": None,
            "error": None,
            "agentic_grade": {
                "relevancy": 0.9,
                "faithfulness": 0.88,
                "context_quality": 0.85,
                "needs_web_search": False,
                "explanation": "Grounded in repository context and retrieved policy evidence.",
                "answer": "High-risk employment AI issue detected.",
                "retrieval_confidence": 0.81,
                "trust_level": "high",
            },
            "retrieval_evidence": [
                {
                    "query": "employment AI protected attributes",
                    "chunk_id": "p1_c0",
                    "page": 1,
                    "confidence": 0.81,
                    "trust_score": 0.79,
                }
            ],
            "web_search_evidence": [],
        }

    monkeypatch.setattr(review_file_module, "assess_file_with_llm", fake_assess_file_with_llm)


def test_graph_streams_violation_events_and_writes_report(tmp_path: Path, monkeypatch) -> None:
    _stub_llm_review(monkeypatch)
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
        "llm_provider": "openrouter",
        "llm_model": "qwen/qwen3.6-plus:free",
        "config": {
            "scan": {"output_dir": "compliance-analysis"},
            "rag": {"top_k": 1},
            "agentic": {"enabled": True},
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
    assert (tmp_path / "DIRECTORY_ANALYSIS.md").exists()
    json.dumps(output["file_result"])


def test_graph_applies_line_offset_to_incremental_snippets(tmp_path: Path, monkeypatch) -> None:
    _stub_llm_review(monkeypatch)
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
        "llm_provider": "openrouter",
        "llm_model": "qwen/qwen3.6-plus:free",
        "line_offset": 9,
        "config": {
            "scan": {"output_dir": "compliance-analysis"},
            "rag": {"top_k": 1},
            "agentic": {"enabled": True},
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
