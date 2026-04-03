from __future__ import annotations

import asyncio
from pathlib import Path

import mcp_server
import nodes.review_file as review_file_module
from graphs.compliance_graph import compile_graph
from mcp_server import _ensure_runtime, stream_compliance_check


def test_stream_compliance_check_yields_custom_and_completion_events(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(review_file_module, "missing_provider_credential", lambda provider: None)
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
                    "remedy": "Remove protected attributes and add human review.",
                    "rag_chunk_id": "p1_c0",
                    "rag_page": 1,
                }
            ],
            "report_path": None,
            "error": None,
            "agentic_grade": None,
            "retrieval_evidence": [],
            "web_search_evidence": [],
        }

    monkeypatch.setattr(review_file_module, "assess_file_with_llm", fake_assess_file_with_llm)

    file_path = tmp_path / "unsafe_hiring.py"
    file_path.write_text(
        """
features = ["gender", "age"]
model.fit(X, y)
# hiring classifier
""".strip(),
        encoding="utf-8",
    )

    graph = compile_graph(
        checkpointer=False,
        config={
            "scan": {"output_dir": "compliance-analysis"},
            "checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")},
        }
    )

    async def collect():
        return [
            event
            async for event in stream_compliance_check(
                graph=graph,
                file_path=str(file_path),
                file_content=file_path.read_text(encoding="utf-8"),
                provider="openrouter",
                model="qwen/qwen3.6-plus:free",
                thread_id="thread-1",
            )
        ]

    events = asyncio.run(collect())

    assert any(event["event"] == "on_custom_event" and event["name"] == "violation_found" for event in events)
    assert any(event["event"] == "on_chain_end" and event["name"] == "write_report" for event in events)


def test_ensure_runtime_logs_and_continues_when_rag_fails(monkeypatch, capsys) -> None:
    monkeypatch.setattr(mcp_server, "needs_ingestion", lambda config: True)

    def fail_ingest(config):
        raise RuntimeError("broken chroma bindings")

    monkeypatch.setattr(mcp_server, "ingest", fail_ingest)

    _ensure_runtime({"rag": {"chroma_persist_dir": ".chroma_db"}})

    captured = capsys.readouterr()
    assert "continuing without RAG" in captured.err
