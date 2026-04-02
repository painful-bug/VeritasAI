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
    assert config["llm"]["default_model"] == "glm4:cloud"
    assert config["rag"]["knowledge_base_pdf"] == str((tmp_path / "knowledge" / "ai_ethics_knowledge_base.pdf").resolve())
    assert config["rag"]["chroma_persist_dir"] == str((tmp_path / ".chroma_db").resolve())
    assert config["checkpoint"]["sqlite_path"] == str((tmp_path / ".langgraph_checkpoints.db").resolve())
    assert config["scan"]["output_dir"] == "compliance-analysis"
    assert config["extension"]["debounce_ms"] == 5000


def test_load_config_defaults_to_repo_root_when_relative_path_is_missing() -> None:
    config = load_config("missing-config.yaml")

    assert Path(config["rag"]["knowledge_base_pdf"]).is_absolute()
    assert Path(config["rag"]["chroma_persist_dir"]).is_absolute()
    assert Path(config["checkpoint"]["sqlite_path"]).is_absolute()
