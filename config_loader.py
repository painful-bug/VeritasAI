from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "llm": {
        "default_provider": "ollama_cloud",
        "default_model": "glm4:cloud",
        "max_retries": 3,
        "retry_backoff_jitter": True,
        "rate_limit_rps": 2,
        "rate_limit_burst": 10,
        "providers": {
            "ollama_cloud": {
                "base_url": "https://cloud.ollama.com",
                "models": ["glm4:cloud", "llama3.3:cloud", "qwen2.5:cloud"],
            },
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["qwen/qwen3.6-plus:free"],
            },
            "groq": {
                "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
            },
            "ollama_local": {
                "base_url": "http://localhost:11434",
                "models": [],
            },
        },
    },
    "rag": {
        "knowledge_base_pdf": "knowledge/ai_ethics_knowledge_base.pdf",
        "chroma_persist_dir": ".chroma_db",
        "collection_name": "ai_ethics_kb",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "top_k": 3,
        "embedding_model": "all-MiniLM-L6-v2",
    },
    "agentic": {
        "enabled": True,
        "runtime_mode": "hybrid",
        "max_retries": 2,
        "retrieval_top_k": 3,
        "retrieval_trust_min": 0.3,
        "web_search_max_results": 3,
        "grade_thresholds": {
            "relevancy_min": 0.55,
            "faithfulness_min": 0.6,
            "context_quality_min": 0.5,
            "force_web_search_relevancy_max": 0.35,
        },
    },
    "scan": {
        "output_dir": "compliance-analysis",
        "max_file_size_mb": 50,
    },
    "directory_analysis": {
        "enabled": True,
        "filename": "DIRECTORY_ANALYSIS.md",
        "preview_chars": 12000,
        "exclude_dirs": [
            ".git",
            ".hg",
            ".svn",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".idea",
            ".vscode",
            ".chroma_db",
            "dist",
            "build",
        ],
        "exclude_globs": [
            ".env",
            ".env.*",
            "*.pyc",
            "*.pyo",
            "*.so",
            "*.dylib",
            "*.dll",
            "*.class",
            "*.jar",
            "*.whl",
            "*.zip",
            "*.tar",
            "*.gz",
            "*.7z",
            "*.lock",
            ".DS_Store",
        ],
    },
    "filesystem": {
        "write_lock_timeout_s": 30,
        "read_retry_attempts": 3,
        "read_retry_min_wait_s": 0.5,
        "read_retry_max_wait_s": 4.0,
    },
    "checkpoint": {
        "backend": "sqlite",
        "sqlite_path": ".langgraph_checkpoints.db",
        "postgres_uri_env": "POSTGRES_URI",
    },
    "langsmith": {
        "project": "ai-ethics-compliance-agent",
        "endpoint": "https://api.smith.langchain.com",
        "tracing_v2": True,
    },
    "extension": {
        "debounce_ms": 5000,
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _resolve_path_like(value: Any, base_dir: Path) -> Any:
    if not isinstance(value, str) or not value.strip():
        return value
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve())
    return str((base_dir / candidate).resolve())


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

    knowledge = normalized.get("knowledge", {})
    rag = normalized.setdefault("rag", {})
    rag.setdefault("knowledge_base_pdf", knowledge.get("pdf_path", "knowledge/ai_ethics_knowledge_base.pdf"))
    rag.setdefault("chroma_persist_dir", rag.get("persist_dir", ".chroma_db"))
    rag.setdefault("persist_dir", rag.get("chroma_persist_dir", ".chroma_db"))
    rag.setdefault("collection_name", "ai_ethics_kb")
    rag.setdefault("top_k", 3)
    rag.setdefault("chunk_size", 500)
    rag.setdefault("chunk_overlap", 50)
    rag.setdefault("embedding_model", "all-MiniLM-L6-v2")

    agentic = normalized.setdefault("agentic", {})
    agentic.setdefault("enabled", True)
    agentic.setdefault("runtime_mode", "hybrid")
    agentic.setdefault("max_retries", 2)
    agentic.setdefault("retrieval_top_k", 3)
    agentic.setdefault("retrieval_trust_min", 0.3)
    agentic.setdefault("web_search_max_results", 3)
    thresholds = agentic.setdefault("grade_thresholds", {})
    thresholds.setdefault("relevancy_min", 0.55)
    thresholds.setdefault("faithfulness_min", 0.6)
    thresholds.setdefault("context_quality_min", 0.5)
    thresholds.setdefault("force_web_search_relevancy_max", 0.35)

    llm = normalized.setdefault("llm", {})
    llm.setdefault("default_provider", "ollama_cloud")
    llm.setdefault("default_model", "glm4:cloud")
    providers = llm.setdefault("providers", {})
    for provider_name in ("ollama_cloud", "openrouter", "groq", "ollama_local"):
        providers.setdefault(provider_name, {})
    providers["ollama_cloud"].setdefault("base_url", "https://cloud.ollama.com")
    providers["ollama_cloud"].setdefault("models", ["glm4:cloud", "llama3.3:cloud", "qwen2.5:cloud"])
    providers["openrouter"].setdefault("base_url", "https://openrouter.ai/api/v1")
    providers["openrouter"].setdefault("models", ["qwen/qwen3.6-plus:free"])
    providers["groq"].setdefault("models", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"])
    providers["ollama_local"].setdefault("base_url", "http://localhost:11434")
    providers["ollama_local"].setdefault("models", [])
    default_provider = str(llm.get("default_provider", "ollama_cloud") or "ollama_cloud")
    available_default_models = list(providers.get(default_provider, {}).get("models", []))
    default_model = str(llm.get("default_model", "") or "").strip()
    if available_default_models and default_model not in available_default_models:
        llm["default_model"] = available_default_models[0]

    scan = normalized.setdefault("scan", {})
    scan.setdefault("output_dir", "compliance-analysis")
    scan.setdefault("max_file_size_mb", 50)

    directory_analysis = normalized.setdefault("directory_analysis", {})
    directory_analysis.setdefault("enabled", True)
    directory_analysis.setdefault("filename", "DIRECTORY_ANALYSIS.md")
    directory_analysis.setdefault("preview_chars", 12000)
    directory_analysis.setdefault(
        "exclude_dirs",
        [
            ".git",
            ".hg",
            ".svn",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".idea",
            ".vscode",
            ".chroma_db",
            "dist",
            "build",
        ],
    )
    directory_analysis.setdefault(
        "exclude_globs",
        [
            ".env",
            ".env.*",
            "*.pyc",
            "*.pyo",
            "*.so",
            "*.dylib",
            "*.dll",
            "*.class",
            "*.jar",
            "*.whl",
            "*.zip",
            "*.tar",
            "*.gz",
            "*.7z",
            "*.lock",
            ".DS_Store",
        ],
    )

    extension = normalized.setdefault("extension", {})
    extension.setdefault("debounce_ms", 5000)

    return normalized


def _resolve_runtime_paths(config: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    resolved = deepcopy(config)

    rag = resolved.setdefault("rag", {})
    rag["knowledge_base_pdf"] = _resolve_path_like(
        rag.get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf"),
        base_dir,
    )
    chroma_persist_dir = _resolve_path_like(rag.get("chroma_persist_dir", ".chroma_db"), base_dir)
    rag["chroma_persist_dir"] = chroma_persist_dir
    rag["persist_dir"] = _resolve_path_like(rag.get("persist_dir", chroma_persist_dir), base_dir)

    checkpoint = resolved.setdefault("checkpoint", {})
    checkpoint["sqlite_path"] = _resolve_path_like(checkpoint.get("sqlite_path", ".langgraph_checkpoints.db"), base_dir)

    return resolved


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = (_repo_root() / config_path).resolve()

    if not config_path.exists():
        return _resolve_runtime_paths(_normalize_aliases(DEFAULT_CONFIG), _repo_root())

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        return _resolve_runtime_paths(_normalize_aliases(DEFAULT_CONFIG), config_path.parent)

    merged = _deep_merge(DEFAULT_CONFIG, raw)
    return _resolve_runtime_paths(_normalize_aliases(merged), config_path.parent)


def save_config(config: dict[str, Any], path: str | Path = "config.yaml") -> None:
    config_path = Path(path)
    with config_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
