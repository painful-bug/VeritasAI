from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "llm": {
        "max_retries": 3,
        "retry_backoff_jitter": True,
        "rate_limit_rps": 2,
        "rate_limit_burst": 10,
    },
    "scan": {
        "max_parallel_agents": 4,
        "max_concurrency": 4,
        "max_file_size_mb": 10,
        "output_dir": "compliance-analysis",
        "excluded_extensions": [],
        "excluded_dirs": [],
    },
    "rag": {
        "persist_dir": ".chroma_db",
        "collection_name": "ai_ethics_kb",
        "chunk_size": 800,
        "chunk_overlap": 120,
        "top_k": 5,
    },
    "review": {
        "llm_inline_content_chars": 30000,
        "llm_rag_query_count": 5,
        "llm_rag_hits_per_query": 3,
    },
    "filesystem": {
        "write_lock_timeout_s": 30,
        "read_retry_attempts": 3,
        "read_retry_min_wait_s": 0.5,
        "read_retry_max_wait_s": 4.0,
        "bash_timeout_s": 60,
        "bash_max_command_length": 1000,
    },
    "checkpoint": {
        "backend": "sqlite",
        "sqlite_path": ".langgraph_checkpoints.db",
        "postgres_uri_env": "POSTGRES_URI",
    },
    "web_search": {
        "max_results": 3,
        "retry_attempts": 3,
        "fallback_provider": "duckduckgo",
    },
    "langsmith": {
        "project": "ai-ethics-compliance-agent",
        "endpoint": "https://api.smith.langchain.com",
        "tracing_v2": True,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged



def _normalize_aliases(config: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(config)

    scan = normalized.setdefault("scan", {})
    if "skip_extensions" in scan and "excluded_extensions" not in scan:
        scan["excluded_extensions"] = scan["skip_extensions"]
    if "excluded_extensions" in scan and "skip_extensions" not in scan:
        scan["skip_extensions"] = scan["excluded_extensions"]
    if "excluded_dirs" in scan and "skip_dirs" not in scan:
        scan["skip_dirs"] = scan["excluded_dirs"]

    knowledge = normalized.get("knowledge", {})
    rag = normalized.setdefault("rag", {})
    rag.setdefault("knowledge_base_pdf", knowledge.get("pdf_path", "knowledge/ai_ethics_knowledge_base.pdf"))
    rag.setdefault("persist_dir", rag.get("chroma_persist_dir", ".chroma_db"))
    rag.setdefault("chroma_persist_dir", rag.get("persist_dir", ".chroma_db"))
    rag.setdefault("collection_name", "ai_ethics_kb")
    rag.setdefault("embedder_provider", knowledge.get("embedder_provider", "ollama"))
    rag.setdefault("embedder_model", knowledge.get("embedder_model", "nomic-embed-text:v1.5"))
    rag.setdefault("top_k", 5)

    llm = normalized.setdefault("llm", {})
    providers = llm.setdefault("providers", {})
    for provider_name, provider_config in providers.items():
        if isinstance(provider_config, dict):
            provider_config.setdefault("models", [])
            if provider_name == "ollama_local":
                provider_config.setdefault("base_url", "http://localhost:11434")
            if provider_name == "ollama_cloud":
                provider_config.setdefault("base_url", "https://cloud.ollama.com")
            if provider_name == "openrouter":
                provider_config.setdefault("base_url", "https://openrouter.ai/api/v1")

    return normalized



def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return _normalize_aliases(deepcopy(DEFAULT_CONFIG))
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    merged = _deep_merge(DEFAULT_CONFIG, raw)
    return _normalize_aliases(merged)



def save_config(config: dict[str, Any], path: str | Path = "config.yaml") -> None:
    config_path = Path(path)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
