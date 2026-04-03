from __future__ import annotations

from llm.provider_factory import missing_provider_credential, resolve_provider_model


def test_resolve_provider_model_falls_back_from_invalid_requested_model() -> None:
    provider, model = resolve_provider_model(
        provider="openrouter",
        model="qwen/qwen3-4b",
        config={
            "llm": {
                "default_provider": "openrouter",
                "default_model": "qwen/qwen3.6-plus:free",
                "providers": {
                    "openrouter": {
                        "models": ["qwen/qwen3.6-plus:free"],
                    }
                },
            }
        },
    )

    assert provider == "openrouter"
    assert model == "qwen/qwen3.6-plus:free"


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

    assert provider == "groq"
    assert model == "llama-3.3-70b-versatile"


def test_missing_provider_credential_returns_required_env_name(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert missing_provider_credential("openrouter") == "OPENROUTER_API_KEY"


def test_missing_provider_credential_returns_none_when_env_present(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "secret")
    assert missing_provider_credential("groq") is None
