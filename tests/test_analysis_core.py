from __future__ import annotations

from pathlib import Path

from analysis.core import analyze_file, extract_data_sources, validate_data_source_reference


def test_extract_data_sources_finds_urls_and_local_paths() -> None:
    content = 'dataset = "./data/applicants.csv"\napi = "https://example.com/data"\n'
    sources = extract_data_sources(content)
    values = {item["url_or_path"] for item in sources}
    assert "./data/applicants.csv" in values
    assert "https://example.com/data" in values


def test_analyze_file_flags_employment_risk(tmp_path: Path) -> None:
    file_path = tmp_path / "train_model.py"
    file_path.write_text(
        """
features = ["gender", "age", "zip code"]
applicants = "./data/applicants.csv"
model.fit(X, y)
# hiring classifier
""".strip(),
        encoding="utf-8",
    )
    config = {"rag": {"top_k": 2}}

    result, pending = analyze_file(str(file_path), "source_code", config)

    assert result["status"] in {"FAIL", "WARN"}
    assert any("employment" in finding["title"].lower() or "protected" in finding["title"].lower() for finding in result["findings"])
    assert pending


def test_analyze_file_attaches_rag_citations(tmp_path: Path) -> None:
    file_path = tmp_path / "unsafe_hiring.py"
    file_path.write_text(
        """
features = ["gender", "age", "zip code"]
print("candidate rejected")
# hiring model
""".strip(),
        encoding="utf-8",
    )

    result, _ = analyze_file(
        str(file_path),
        "source_code",
        {"rag": {"top_k": 1}},
        query_rag=lambda description, top_k: [
            {"text": "employment-related KB text", "metadata": {"chunk_id": "p7_c2", "page": 7}}
        ],
    )

    assert result["findings"]
    assert any(finding["rag_chunk_id"] == "p7_c2" and finding["rag_page"] == 7 for finding in result["findings"])


def test_validate_data_source_handles_missing_local_path(tmp_path: Path) -> None:
    source = {"url_or_path": "./data/faces_scraped.csv", "source_type": "local_path", "context": "training data"}
    result = validate_data_source_reference(source, current_file="main.py", target_directory=str(tmp_path), config={"rag": {"top_k": 1}})
    assert result["verdict"] in {"FAIL", "WARN", "UNKNOWN"}
    assert result["path_exists"] is False
