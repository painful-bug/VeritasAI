from __future__ import annotations

import os
from typing import Any

from langsmith import Client


def _tracing_enabled() -> bool:
    if not os.getenv("LANGSMITH_API_KEY"):
        return False
    flag = os.getenv("LANGSMITH_TRACING_V2", "true").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def get_langsmith_tracer(run_name: str | None = None):
    if not _tracing_enabled():
        return None
    try:
        from langchain.callbacks.tracers import LangChainTracer

        project = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")
        return LangChainTracer(project_name=project, run_name=run_name)
    except Exception:
        return None


def get_run_config(thread_id: str, file_path: str, provider: str, model: str) -> dict[str, Any]:
    tracer = get_langsmith_tracer(run_name=f"check-{thread_id}")
    callbacks = [tracer] if tracer else []
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": callbacks,
        "tags": ["compliance-scan", f"provider:{provider}", f"model:{model}"],
        "metadata": {
            "thread_id": thread_id,
            "file_path": file_path,
            "llm_provider": provider,
            "llm_model": model,
        },
        "run_name": f"ComplianceCheck-{thread_id[:8]}",
    }


def resolve_run_url(run_id: str | None) -> str | None:
    if not run_id or not _tracing_enabled():
        return None
    try:
        client = Client()
        run = client.read_run(run_id)
        return client.get_run_url(run=run)
    except Exception:
        return None
