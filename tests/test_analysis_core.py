from __future__ import annotations

from pathlib import Path

from analysis.core import analyze_file, extract_data_sources


def test_extract_data_sources_finds_urls_and_local_paths() -> None:
    content = 'dataset = "./data/applicants.csv"\napi = "https://example.com/data"\n'
    sources = extract_data_sources(content)
    values = {item["url_or_path"] for item in sources}
    assert "./data/applicants.csv" in values
    assert "https://example.com/data" in values


def test_analyze_file_prepares_review_metadata_without_heuristic_findings(tmp_path: Path) -> None:
    file_path = tmp_path / "unsafe_hiring.py"
    file_path.write_text(
        """
features = ["gender", "age", "zip_code"]
applicants = "./data/applicants.csv"
model.fit(X, y)
# hiring classifier
""".strip(),
        encoding="utf-8",
    )

    result, sources = analyze_file(
        str(file_path),
        config={"rag": {"top_k": 1}},
        file_content=file_path.read_text(encoding="utf-8"),
    )

    assert result["status"] == "PASS"
    assert result["findings"] == []
    assert "structural context for the LLM review" in result["summary"]
    assert result["predicted_output"]
    assert sources


def test_analyze_file_skips_directory_analysis_artifact(tmp_path: Path) -> None:
    file_path = tmp_path / "DIRECTORY_ANALYSIS.md"
    file_path.write_text("# Directory Analysis\n", encoding="utf-8")

    result, sources = analyze_file(
        str(file_path),
        config={"directory_analysis": {"filename": "DIRECTORY_ANALYSIS.md"}},
        file_content=file_path.read_text(encoding="utf-8"),
    )

    assert result["status"] == "SKIPPED"
    assert "agent-generated repository context" in result["summary"]
    assert sources == []


def test_analyze_file_skips_non_target_config_files(tmp_path: Path) -> None:
    file_path = tmp_path / "settings.toml"
    file_path.write_text("model = 'demo'\n", encoding="utf-8")

    result, sources = analyze_file(
        str(file_path),
        file_content=file_path.read_text(encoding="utf-8"),
    )

    assert result["status"] == "SKIPPED"
    assert "only source code, documents, and structured data are reviewed" in result["summary"]
    assert sources == []
