from __future__ import annotations

from analysis.reports import build_file_report_markdown


def test_build_file_report_markdown_matches_prd_sections() -> None:
    markdown = build_file_report_markdown(
        {
            "file_path": "/tmp/train_model.py",
            "file_type": "source_code",
            "language": "Python",
            "status": "FAIL",
            "summary": "Trains a hiring model.",
            "predicted_output": "Produces a classifier.",
            "findings": [
                {
                    "severity": "HIGH",
                    "file_path": "/tmp/train_model.py",
                    "start_line": 1,
                    "end_line": 3,
                    "regulation_name": "EU AI Act — Article 10 Data and Data Governance",
                    "jurisdiction": "EU",
                    "explanation": "Uses gender and age in a hiring pipeline.",
                    "remedy": "Remove protected attributes from the automated decision path.",
                    "rag_chunk_id": "p1_c1",
                    "rag_page": 1,
                }
            ],
            "report_path": None,
            "error": None,
        }
    )

    assert "# Compliance Report: /tmp/train_model.py" in markdown
    assert "## Findings" in markdown
    assert "[HIGH] EU AI Act — Article 10 Data and Data Governance" in markdown
    assert "**Remedy:** Remove protected attributes from the automated decision path." in markdown
