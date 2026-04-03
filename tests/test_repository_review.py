from __future__ import annotations

from pathlib import Path

from analysis.repository_review import ensure_directory_analysis


def test_ensure_directory_analysis_creates_markdown_and_skips_ignored_paths(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Example repository for AI ethics checks.", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        """
from pathlib import Path


def run():
    return Path("data/records.csv").read_text()
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "records.csv").write_text("user_id,score\n1,10\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "pyvenv.cfg").write_text("home = /tmp/python\n", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET_TOKEN=hidden\n", encoding="utf-8")
    (tmp_path / "settings.toml").write_text("model = 'demo'\n", encoding="utf-8")

    result = ensure_directory_analysis(tmp_path, config={"scan": {"output_dir": "compliance-analysis"}})

    analysis_path = Path(result["analysis_path"])
    assert result["updated"] is True
    assert analysis_path.exists()
    assert "Repository Overview" in result["content"]
    assert "src/main.py" in result["content"]
    assert "data/records.csv" in result["content"]
    assert ".venv" not in result["content"]
    assert ".env" not in result["content"]
    assert "settings.toml" not in result["content"]


def test_ensure_directory_analysis_reuses_existing_file_and_refreshes_on_repo_change(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("Repository under active development.", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")

    first = ensure_directory_analysis(tmp_path, config={"scan": {"output_dir": "compliance-analysis"}})
    second = ensure_directory_analysis(tmp_path, config={"scan": {"output_dir": "compliance-analysis"}})

    assert first["updated"] is True
    assert second["updated"] is False

    (tmp_path / "new_module.py").write_text("def build():\n    return 1\n", encoding="utf-8")
    third = ensure_directory_analysis(tmp_path, config={"scan": {"output_dir": "compliance-analysis"}})

    assert third["updated"] is True
    assert "new_module.py" in third["content"]
    assert third["snapshot_hash"] != second["snapshot_hash"]
