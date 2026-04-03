from __future__ import annotations

import nodes.review_file as review_file_module


def test_review_file_node_returns_actionable_error_for_missing_provider_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(review_file_module, "dispatch_custom_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(review_file_module, "_rag_query", lambda config: (lambda description, top_k: []))

    state = {
        "file_path": "/tmp/example.py",
        "file_content": "model.fit(X, y)\n# hiring classifier\n",
        "config": {"agentic": {"enabled": True}, "rag": {"top_k": 3}},
        "llm_provider": "openrouter",
        "llm_model": "qwen/qwen3.6-plus:free",
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }

    result = review_file_module.review_file_node(state, {})
    file_result = result["file_result"]

    assert file_result["status"] == "ERROR"
    assert "OPENROUTER_API_KEY" in (file_result["error"] or "")
