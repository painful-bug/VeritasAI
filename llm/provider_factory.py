from __future__ import annotations

import os
import subprocess
from typing import Any

_LLM_CACHE: dict[tuple[str, str, str, float], Any] = {}



def _make_rate_limiter(config: dict[str, Any]):
    try:
        from langchain_core.rate_limiters import InMemoryRateLimiter
    except Exception:
        return None

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
            check=True,
            timeout=8,
        ).stdout
    except Exception:
        return []

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    models: list[str] = []
    for line in lines[1:]:
        model = line.split()[0]
        if model:
            models.append(model)
    return models



def get_available_models(config: dict[str, Any], provider: str) -> list[str]:
    provider_config = config.get("llm", {}).get("providers", {}).get(provider, {})
    models = list(provider_config.get("models", []))
    if provider == "ollama_local":
        dynamic = [model for model in list_local_ollama_models() if model not in models]
        models.extend(dynamic)
    return models



def create_llm(provider: str, model: str, config: dict[str, Any], **kwargs: Any):
    llm_config = config.get("llm", {})
    temperature = kwargs.pop("temperature", llm_config.get("temperature", 0.1))
    retries = int(llm_config.get("max_retries", 3))
    provider_config = config.get("llm", {}).get("providers", {}).get(provider, {})
    base_url = str(provider_config.get("base_url", ""))
    cache_key = (provider, model, base_url, float(temperature))
    if cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    rate_limiter = _make_rate_limiter(config)

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama

        base_url = provider_config.get("base_url", "https://cloud.ollama.com")
        llm = ChatOllama(
            model=model,
            base_url=base_url,
            api_key=os.getenv("OLLAMA_CLOUD_API_KEY"),
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI

        base_url = provider_config.get("base_url", "https://openrouter.ai/api/v1")
        llm = ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=temperature,
            default_headers={"HTTP-Referer": "https://local.ethics-agent", "X-Title": "AI Ethics Compliance Agent"},
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

        base_url = provider_config.get("base_url", "http://localhost:11434")
        llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            rate_limiter=rate_limiter,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if hasattr(llm, "with_retry"):
        try:
            retriable = llm.with_retry(stop_after_attempt=retries, wait_exponential_jitter=True)
            if hasattr(retriable, "bind_tools"):
                llm = retriable
        except Exception:
            pass
    _LLM_CACHE[cache_key] = llm
    return llm



def try_create_llm(provider: str, model: str, config: dict[str, Any]):
    try:
        return create_llm(provider, model, config)
    except Exception:
        return None



def test_connection(provider: str, model: str, config: dict[str, Any]) -> tuple[bool, str]:
    required_key = provider_requires_api_key(provider)
    if required_key and not os.getenv(required_key):
        return False, f"Missing environment variable: {required_key}"

    try:
        llm = create_llm(provider, model, config)
        response = llm.invoke("Reply with exactly: OK")
        content = getattr(response, "content", str(response))
        return True, str(content).strip() or "OK"
    except Exception as exc:
        return False, str(exc)
