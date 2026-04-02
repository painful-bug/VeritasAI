from __future__ import annotations

from pathlib import Path

from analysis.core import analyze_file, extract_data_sources


def test_extract_data_sources_finds_urls_and_local_paths() -> None:
    content = 'dataset = "./data/applicants.csv"\napi = "https://example.com/data"\n'
    sources = extract_data_sources(content)
    values = {item["url_or_path"] for item in sources}
    assert "./data/applicants.csv" in values
    assert "https://example.com/data" in values


def test_analyze_file_flags_employment_risk_and_attaches_rag_metadata(tmp_path: Path) -> None:
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
        query_rag=lambda description, top_k: [
            {"text": "employment-related KB text", "metadata": {"chunk_id": "p7_c2", "page": 7}}
        ],
        file_content=file_path.read_text(encoding="utf-8"),
    )

    assert result["status"] == "FAIL"
    assert any(finding["severity"] == "HIGH" for finding in result["findings"])
    assert any(finding["rag_chunk_id"] == "p7_c2" and finding["rag_page"] == 7 for finding in result["findings"])
    assert sources
