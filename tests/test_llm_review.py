from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from analysis.llm_review import assess_file_with_llm


class StubLLM:
    def __init__(self, final_payload: str):
        self.final_payload = final_payload

    def invoke(self, prompt: str):
        if "TASK: RAG_QUERY_GENERATION" in prompt:
            return SimpleNamespace(
                content=(
                    '<RESULT>{"queries": ['
                    '"automated hiring decision using demographic attributes gender age"], '
                    '"notes": ["query generated from file content"]}</RESULT>'
                )
            )
        if "TASK: FINAL_FILE_ASSESSMENT" in prompt:
            return SimpleNamespace(content=self.final_payload)
        raise AssertionError(f"Unexpected prompt: {prompt[:120]}")


def sample_base_result(file_path: str) -> dict:
    return {
        "file_path": file_path,
        "file_type": "source_code",
        "language": "Python",
        "status": "PASS",
        "summary": "Initial deterministic summary.",
        "predicted_output": "Initial predicted output.",
        "findings": [],
        "data_sources": [],
        "report_path": None,
        "error": None,
        "notes": ["Initial note."],
    }


def test_assess_file_with_llm_returns_fail_when_rag_grounded_violation_exists(tmp_path: Path) -> None:
    file_path = tmp_path / "unsafe_hiring.py"
    file_path.write_text(
        'features = ["gender", "age"]\nprint("reject candidate")\n',
        encoding="utf-8",
    )

    llm = StubLLM(
        '<RESULT>{'
        '"summary": "The file screens applicants using protected attributes.", '
        '"predicted_output": "Produces hiring decisions.", '
        '"status": "FAIL", '
        '"notes": ["LLM reviewed the whole file."], '
        '"findings": ['
        '{'
        '"title": "Protected attributes used in automated employment context", '
        '"severity": "HIGH", '
        '"start_line": 1, '
        '"end_line": 1, '
        '"section_desc": "Line 1", '
        '"regulations": ["EU AI Act Article 10"], '
        '"jurisdictions": ["European Union"], '
        '"explanation": "The file uses gender and age in automated applicant screening.", '
        '"rag_chunk_id": "p4_c0", '
        '"rag_page": 4'
        '}'
        ']}</RESULT>'
    )

    result = assess_file_with_llm(
        llm=llm,
        file_path=str(file_path),
        file_type="source_code",
        base_result=sample_base_result(str(file_path)),
        config={"review": {"llm_inline_content_chars": 30000, "llm_rag_query_count": 3, "llm_rag_hits_per_query": 2}},
        query_rag=lambda description, top_k: [
            {"text": "Employment-related AI regulation excerpt", "metadata": {"chunk_id": "p4_c0", "page": 4}}
        ],
    )

    assert result is not None
    assert result["status"] == "FAIL"
    assert result["findings"][0]["rag_chunk_id"] == "p4_c0"
    assert result["findings"][0]["rag_page"] == 4
    assert "LLM review grounded in retrieved RAG excerpts" in result["notes"][-1]


def test_assess_file_with_llm_returns_pass_when_no_rule_is_violated(tmp_path: Path) -> None:
    file_path = tmp_path / "helpers.py"
    file_path.write_text('def slugify(value):\n    return value.lower()\n', encoding="utf-8")

    llm = StubLLM(
        '<RESULT>{'
        '"summary": "Utility helper with no AI decision logic.", '
        '"predicted_output": "Formats strings.", '
        '"status": "PASS", '
        '"notes": ["No applicable AI act violation found."], '
        '"findings": []}</RESULT>'
    )

    result = assess_file_with_llm(
        llm=llm,
        file_path=str(file_path),
        file_type="source_code",
        base_result=sample_base_result(str(file_path)),
        config={"review": {"llm_inline_content_chars": 30000, "llm_rag_query_count": 3, "llm_rag_hits_per_query": 2}},
        query_rag=lambda description, top_k: [
            {"text": "General governance excerpt", "metadata": {"chunk_id": "p1_c0", "page": 1}}
        ],
    )

    assert result is not None
    assert result["status"] == "PASS"
    assert result["findings"] == []
    assert result["summary"] == "Utility helper with no AI decision logic."
