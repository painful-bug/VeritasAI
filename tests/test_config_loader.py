from __future__ import annotations

from pathlib import Path

from config_loader import load_config



def test_load_config_adds_runtime_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
llm:
  default_provider: openrouter
  default_model: qwen/qwen3.6-plus-preview:free
knowledge:
  pdf_path: knowledge/ai_ethics_knowledge_base.pdf
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["llm"]["default_provider"] == "openrouter"
    assert config["llm"]["default_model"] == "qwen/qwen3.6-plus-preview:free"
    assert config["scan"]["output_dir"] == "compliance-analysis"
    assert config["rag"]["knowledge_base_pdf"] == "knowledge/ai_ethics_knowledge_base.pdf"
    assert config["checkpoint"]["sqlite_path"] == ".langgraph_checkpoints.db"
