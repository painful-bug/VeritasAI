from __future__ import annotations

import os
from typing import Any



def _tracing_enabled() -> bool:
    flags = (
        os.getenv("LANGSMITH_TRACING"),
        os.getenv("LANGSMITH_TRACING_V2"),
        os.getenv("LANGCHAIN_TRACING_V2"),
    )
    normalized = [flag.strip().lower() for flag in flags if isinstance(flag, str) and flag.strip()]
    if not normalized:
        return True
    return any(flag not in {"0", "false", "no", "off"} for flag in normalized)


def get_langsmith_tracer(run_name: str | None = None):
    del run_name
    if not _tracing_enabled():
        return None
    try:
        from langchain.callbacks.tracers import LangChainTracer
    except Exception:
        return None

    project = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")
    return LangChainTracer(project_name=project)



def get_run_config(thread_id: str, target_dir: str, provider: str, model: str) -> dict[str, Any]:
    tracer = get_langsmith_tracer(run_name=f"scan-{thread_id}")
    callbacks = [tracer] if tracer else []
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": callbacks,
        "tags": ["compliance-scan", f"provider:{provider}", f"model:{model}"],
        "metadata": {
            "thread_id": thread_id,
            "target_directory": target_dir,
            "llm_provider": provider,
            "llm_model": model,
        },
        "run_name": f"ComplianceScan-{thread_id[:8]}",
    }
