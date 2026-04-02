from __future__ import annotations

from analysis.reports import build_file_report_markdown, build_final_report_markdown, build_report_context



def sample_file_result() -> dict:
    return {
        "file_path": "/tmp/train_model.py",
        "file_type": "source_code",
        "language": "Python",
        "status": "FAIL",
        "summary": "Trains a hiring model.",
        "predicted_output": "Produces a classifier.",
        "findings": [
            {
                "id": "F001",
                "title": "Protected attributes used in automated employment context",
                "severity": "HIGH",
                "file_path": "/tmp/train_model.py",
                "start_line": 1,
                "end_line": 1,
                "section_desc": "Line 1",
                "regulations": ["EU AI Act Article 10"],
                "jurisdictions": ["European Union"],
                "explanation": "Uses gender and age in a hiring pipeline.",
                "rag_chunk_id": "p1_c1",
                "rag_page": 1,
            }
        ],
        "data_sources": [],
        "report_path": "/tmp/train_model_analysis_report.md",
        "error": None,
        "notes": ["Detected fields: gender, age"],
    }



def test_build_file_report_markdown_contains_key_sections() -> None:
    markdown = build_file_report_markdown(sample_file_result())
    assert "## Findings" in markdown
    assert "Protected attributes used in automated employment context" in markdown
    assert "Knowledge base citation" in markdown
    assert "`p1_c1` on page 1" in markdown



def test_build_final_report_markdown_contains_summary_table() -> None:
    context = build_report_context("/tmp", [sample_file_result()], "openrouter", "qwen/qwen3.6-plus-preview:free")
    markdown = build_final_report_markdown(context)
    assert "## Overall Results" in markdown
    assert "## Critical Findings" in markdown
