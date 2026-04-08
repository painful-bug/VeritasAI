from __future__ import annotations

import sys
from types import ModuleType

import llm.provider_factory as provider_factory
from llm.provider_factory import create_llm, missing_provider_credential, resolve_provider_model


def test_resolve_provider_model_preserves_explicit_requested_model() -> None:
    provider, model = resolve_provider_model(
        provider="openrouter",
        model="qwen/qwen3-4b",
        config={
            "llm": {
                "default_provider": "openrouter",
                "default_model": "nvidia/nemotron-3-super-120b-a12b:free",
                "providers": {
                    "openrouter": {
                        "models": ["nvidia/nemotron-3-super-120b-a12b:free"],
                    }
                },
            }
        },
    )

    assert provider == "openrouter"
    assert model == "qwen/qwen3-4b"


def test_resolve_provider_model_falls_back_from_unknown_provider() -> None:
    provider, model = resolve_provider_model(
        provider="unknown_provider",
        model="",
        config={
            "llm": {
                "default_provider": "groq",
                "default_model": "llama-3.3-70b-versatile",
                "providers": {
                    "groq": {
                        "models": ["llama-3.3-70b-versatile"],
                    }
                },
            }
        },
    )

    assert provider == "unknown_provider"
    assert model == "llama-3.3-70b-versatile"


def test_resolve_provider_model_uses_configured_default_model_when_no_request_given() -> None:
    provider, model = resolve_provider_model(
        provider="",
        model="",
        config={
            "llm": {
                "default_provider": "ollama_cloud",
                "default_model": "qwen3.5:cloud",
                "providers": {
                    "ollama_cloud": {
                        "models": ["qwen2.5:cloud"],
                    }
                },
            }
        },
    )

    assert provider == "ollama_cloud"
    assert model == "qwen3.5:cloud"


def test_missing_provider_credential_returns_required_env_name(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert missing_provider_credential("openrouter") == "OPENROUTER_API_KEY"


def test_missing_provider_credential_returns_none_when_env_present(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "secret")
    assert missing_provider_credential("groq") is None


def test_missing_provider_credential_accepts_legacy_ollama_cloud_env(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_CLOUD_API_KEY", "legacy-secret")

    assert missing_provider_credential("ollama_cloud") is None


def test_create_llm_normalizes_ollama_cloud_url_and_sets_bearer_auth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeChatOllama:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def with_retry(self, **kwargs):
            return self

    fake_module = ModuleType("langchain_ollama")
    fake_module.ChatOllama = FakeChatOllama
    monkeypatch.setitem(sys.modules, "langchain_ollama", fake_module)
    monkeypatch.setenv("OLLAMA_CLOUD_API_KEY", "legacy-secret")
    provider_factory._LLM_CACHE.clear()

    llm = create_llm(
        provider="ollama_cloud",
        model="qwen3.5:cloud",
        config={
            "llm": {
                "max_retries": 1,
                "rate_limit_rps": 1,
                "rate_limit_burst": 1,
                "providers": {
                    "ollama_cloud": {
                        "base_url": "https://cloud.ollama.com/api",
                        "models": ["qwen3.5:cloud"],
                    }
                },
            }
        },
    )

    assert isinstance(llm, FakeChatOllama)
    assert captured["base_url"] == "https://ollama.com"
    assert captured["client_kwargs"] == {"headers": {"Authorization": "Bearer legacy-secret"}}


def test_create_llm_normalizes_ollama_local_url(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeChatOllama:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def with_retry(self, **kwargs):
            return self

    fake_module = ModuleType("langchain_ollama")
    fake_module.ChatOllama = FakeChatOllama
    monkeypatch.setitem(sys.modules, "langchain_ollama", fake_module)
    provider_factory._LLM_CACHE.clear()

    llm = create_llm(
        provider="ollama_local",
        model="llama3.2",
        config={
            "llm": {
                "max_retries": 1,
                "rate_limit_rps": 1,
                "rate_limit_burst": 1,
                "providers": {
                    "ollama_local": {
                        "base_url": "http://localhost:11434/api",
                        "models": ["llama3.2"],
                    }
                },
            }
        },
    )

    assert isinstance(llm, FakeChatOllama)
    assert captured["base_url"] == "http://localhost:11434"
