from __future__ import annotations

import os
import subprocess
from typing import Any

from config_loader import load_config

_LLM_CACHE: dict[tuple[str, str, str], Any] = {}
_KNOWN_PROVIDERS = ("ollama_cloud", "openrouter", "groq", "ollama_local")


def _make_rate_limiter(config: dict[str, Any]):
    from langchain_core.rate_limiters import InMemoryRateLimiter

    llm_config = config.get("llm", {})
    return InMemoryRateLimiter(
        requests_per_second=float(llm_config.get("rate_limit_rps", 2)),
        max_bucket_size=int(llm_config.get("rate_limit_burst", 10)),
    )


def provider_requires_api_key(provider: str) -> str | None:
    return {
        "ollama_cloud": "OLLAMA_CLOUD_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "groq": "GROQ_API_KEY",
        "ollama_local": None,
    }.get(provider)


def list_local_ollama_models() -> list[str]:
    try:
        output = subprocess.run(
            ["ollama", "list"],
            text=True,
            capture_output=True,
            timeout=8,
            check=True,
        ).stdout
    except Exception:
        return []

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return [line.split()[0] for line in lines[1:] if line.split()]


def get_available_models(config: dict[str, Any] | None, provider: str) -> list[str]:
    effective = config or load_config()
    models = list(effective.get("llm", {}).get("providers", {}).get(provider, {}).get("models", []))
    if provider == "ollama_local":
        for model in list_local_ollama_models():
            if model not in models:
                models.append(model)
    return models


def resolve_provider_model(provider: str, model: str, config: dict[str, Any] | None = None) -> tuple[str, str]:
    effective = config or load_config()
    llm_config = effective.get("llm", {}) or {}
    configured_providers = llm_config.get("providers", {}) or {}
    default_provider = str(llm_config.get("default_provider", "ollama_cloud") or "ollama_cloud").strip()
    requested_provider = str(provider or "").strip() or default_provider
    known_providers = set(configured_providers) | set(_KNOWN_PROVIDERS)

    if requested_provider not in known_providers:
        requested_provider = default_provider

    available_models = get_available_models(effective, requested_provider)
    requested_model = str(model or "").strip()
    configured_default_model = str(llm_config.get("default_model", "") or "").strip()

    if requested_model and (not available_models or requested_model in available_models):
        return requested_provider, requested_model

    if requested_provider == default_provider and configured_default_model:
        if not available_models or configured_default_model in available_models:
            return requested_provider, configured_default_model

    if available_models:
        return requested_provider, available_models[0]

    if requested_model:
        return requested_provider, requested_model

    return requested_provider, configured_default_model


def create_llm(provider: str, model: str, config: dict[str, Any] | None = None, **kwargs: Any):
    effective = config or load_config()
    provider, model = resolve_provider_model(provider, model, effective)
    provider_config = effective.get("llm", {}).get("providers", {}).get(provider, {})
    base_url = str(provider_config.get("base_url", ""))
    cache_key = (provider, model, base_url)
    if cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    rate_limiter = _make_rate_limiter(effective)
    retries = int(effective.get("llm", {}).get("max_retries", 3))
    temperature = kwargs.pop("temperature", 0)

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=model,
            base_url=base_url or "https://cloud.ollama.com",
            api_key=os.getenv("OLLAMA_CLOUD_API_KEY"),
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            base_url=base_url or "https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            default_headers={
                "HTTP-Referer": "https://local.ai-ethics-agent",
                "X-Title": "AI Ethics Compliance Agent",
            },
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "ollama_local":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=model,
            base_url=base_url or "http://localhost:11434",
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if hasattr(llm, "with_retry"):
        try:
            llm = llm.with_retry(stop_after_attempt=retries, wait_exponential_jitter=True)
        except Exception:
            pass

    _LLM_CACHE[cache_key] = llm
    return llm


def try_create_llm(provider: str, model: str, config: dict[str, Any] | None = None):
    try:
        return create_llm(provider, model, config=config)
    except Exception:
        return None
