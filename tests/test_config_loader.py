from __future__ import annotations

from pathlib import Path

from config_loader import load_config


def test_load_config_adds_prd_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
llm:
  default_provider: openrouter
knowledge:
  pdf_path: knowledge/ai_ethics_knowledge_base.pdf
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["llm"]["default_provider"] == "openrouter"
    assert config["llm"]["default_model"] == "nvidia/nemotron-3-super-120b-a12b:free"
    assert config["rag"]["knowledge_base_pdf"] == str((tmp_path / "knowledge" / "ai_ethics_knowledge_base.pdf").resolve())
    assert config["rag"]["chroma_persist_dir"] == str((tmp_path / ".chroma_db").resolve())
    assert config["checkpoint"]["sqlite_path"] == str((tmp_path / ".langgraph_checkpoints.db").resolve())
    assert config["scan"]["output_dir"] == "compliance-analysis"
    assert config["directory_analysis"]["enabled"] is True
    assert config["directory_analysis"]["filename"] == "DIRECTORY_ANALYSIS.md"
    assert config["extension"]["debounce_ms"] == 5000
    assert config["llm"]["providers"]["ollama_cloud"]["base_url"] == "https://ollama.com"
    assert config["llm"]["providers"]["ollama_local"]["base_url"] == "http://localhost:11434"


def test_load_config_defaults_to_repo_root_when_relative_path_is_missing() -> None:
    config = load_config("missing-config.yaml")

    assert Path(config["rag"]["knowledge_base_pdf"]).is_absolute()
    assert Path(config["rag"]["chroma_persist_dir"]).is_absolute()
    assert Path(config["checkpoint"]["sqlite_path"]).is_absolute()


def test_load_config_allows_environment_to_override_default_provider_and_model(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("llm:\n  default_provider: openrouter\n", encoding="utf-8")
    monkeypatch.setenv("AI_ETHICS_DEFAULT_PROVIDER", "groq")
    monkeypatch.setenv("AI_ETHICS_DEFAULT_MODEL", "mixtral-8x7b-32768")

    config = load_config(config_path)

    assert config["llm"]["default_provider"] == "groq"
    assert config["llm"]["default_model"] == "mixtral-8x7b-32768"


def test_load_config_preserves_environment_default_model_even_if_not_in_static_provider_list(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
llm:
  default_provider: ollama_cloud
  providers:
    ollama_cloud:
      models:
        - qwen2.5:cloud
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_ETHICS_DEFAULT_PROVIDER", "ollama_cloud")
    monkeypatch.setenv("AI_ETHICS_DEFAULT_MODEL", "qwen3.5:cloud")

    config = load_config(config_path)

    assert config["llm"]["default_provider"] == "ollama_cloud"
    assert config["llm"]["default_model"] == "qwen3.5:cloud"


def test_load_config_normalizes_legacy_ollama_urls(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
llm:
  providers:
    ollama_cloud:
      base_url: https://cloud.ollama.com
    ollama_local:
      base_url: http://localhost:11434/api
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["llm"]["providers"]["ollama_cloud"]["base_url"] == "https://ollama.com"
    assert config["llm"]["providers"]["ollama_local"]["base_url"] == "http://localhost:11434"
