from __future__ import annotations

from analysis.llm_review import assess_file_with_llm


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        assert prompt
        self.prompts.append(prompt)
        if not self._responses:
            raise RuntimeError("No fake responses left")
        return self._responses.pop(0)


def _base_result(file_path: str) -> dict:
    return {
        "file_path": file_path,
        "file_type": "source_code",
        "language": "Python",
        "status": "PASS",
        "summary": "Prepared file summary",
        "predicted_output": "Produces predictions.",
        "findings": [],
        "report_path": None,
        "error": None,
    }


def test_assess_file_with_llm_runs_web_augmentation_when_needed() -> None:
    file_path = "/tmp/example.py"
    llm = FakeLLM(
        [
            (
                '<r>{"Relevancy":0.2,"Faithfulness":0.8,"Context Quality":0.4,'
                '"Needs Web Search":true,"Explanation":"Need more context","Answer":"First pass",'
                '"status":"WARN","summary":"first","findings":[]}</r>'
            ),
            (
                '<r>{"Relevancy":0.91,"Faithfulness":0.88,"Context Quality":0.86,'
                '"Needs Web Search":false,"Explanation":"Grounded with RAG and web","Answer":"Final",'
                '"status":"FAIL","summary":"final","findings":[{"severity":"HIGH",'
                '"start_line":10,"end_line":12,"regulation_name":"EU AI Act — Article 10 Data and Data Governance",'
                '"jurisdiction":"EU","explanation":"Protected attributes in hiring",'
                '"remedy":"Remove protected attributes","rag_chunk_id":"p1_c0","rag_page":1}]}</r>'
            ),
        ]
    )

    def query_rag(description: str, top_k: int):
        assert description
        assert top_k == 3
        return [
            {
                "text": "Article 10 requires data governance safeguards.",
                "metadata": {"chunk_id": "p1_c0", "page": 1, "jurisdiction": "EU"},
                "score": 0.21,
                "confidence": 0.82,
                "trust_score": 0.77,
                "query": "compliance",
            }
        ]

    def web_search(query: str, max_results: int):
        assert query
        assert max_results == 2
        return [
            {
                "source": "tavily",
                "title": "Regulatory guidance",
                "url": "https://example.org/guidance",
                "content": "Recent enforcement guidance for high-risk employment AI.",
            }
        ]

    result = assess_file_with_llm(
        llm=llm,
        file_path=file_path,
        file_content="model.fit(X, y)\n# hiring classifier",
        base_result=_base_result(file_path),
        query_rag=query_rag,
        top_k=3,
        provider="openrouter",
        model="qwen/qwen3.6-plus:free",
        config={
            "agentic": {
                "runtime_mode": "hybrid",
                "web_search_max_results": 2,
                "grade_thresholds": {
                    "relevancy_min": 0.55,
                    "faithfulness_min": 0.6,
                    "context_quality_min": 0.5,
                    "force_web_search_relevancy_max": 0.35,
                },
            }
        },
        web_search_fn=web_search,
    )

    assert result is not None
    assert result["status"] == "FAIL"
    assert result["agentic_grade"]["relevancy"] == 0.91
    assert result["agentic_grade"]["needs_web_search"] is False
    assert result["retrieval_evidence"]
    assert result["web_search_evidence"]
    assert result["findings"][0]["rag_chunk_id"] == "p1_c0"


def test_assess_file_with_llm_returns_error_when_model_response_is_invalid() -> None:
    file_path = "/tmp/example.py"
    llm = FakeLLM(["not valid tagged json"])

    result = assess_file_with_llm(
        llm=llm,
        file_path=file_path,
        file_content="print('ok')",
        base_result=_base_result(file_path),
        query_rag=lambda description, top_k: [],
        top_k=3,
        provider="openrouter",
        model="qwen/qwen3.6-plus:free",
        config={"agentic": {"runtime_mode": "hybrid", "grade_thresholds": {}}},
        web_search_fn=None,
    )

    assert result["status"] == "ERROR"
    assert result["findings"] == []
    assert "did not contain valid <r>...</r> JSON" in (result["error"] or "")


def test_assess_file_with_llm_includes_repository_analysis_context() -> None:
    file_path = "/tmp/example.py"
    llm = FakeLLM(
        [
            (
                '<r>{"Relevancy":0.8,"Faithfulness":0.9,"Context Quality":0.8,'
                '"Needs Web Search":false,"Explanation":"Enough context","Answer":"ok",'
                '"status":"WARN","summary":"kept","findings":[]}</r>'
            )
        ]
    )

    reviewed_context = [
        {
            "start_line": 10,
            "end_line": 20,
            "summary": "Previous scan found automated scoring nearby.",
            "findings": _base_result(file_path)["findings"],
        }
    ]
    repository_context = """
# Directory Analysis

- Purpose: Repository coordinates AI ethics scanning, report writing, and a VS Code integration.
- Main themes: compliance, diagnostics, repository review
""".strip()

    result = assess_file_with_llm(
        llm=llm,
        file_path=file_path,
        file_content="print('ok')",
        base_result=_base_result(file_path),
        query_rag=lambda description, top_k: [],
        top_k=3,
        provider="openrouter",
        model="qwen/qwen3.6-plus:free",
        config={"agentic": {"runtime_mode": "llm", "grade_thresholds": {}}},
        web_search_fn=None,
        reviewed_context=reviewed_context,
        repository_context=repository_context,
    )

    assert llm.prompts
    assert "You are the final compliance reviewer" in llm.prompts[0]
    assert "Repository-wide DIRECTORY_ANALYSIS context" in llm.prompts[0]
    assert "VS Code integration" in llm.prompts[0]
    assert "Nearby reviewed context" in llm.prompts[0]
