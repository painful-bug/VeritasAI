from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import NotRequired, TypedDict


class AgenticGrade(TypedDict):
    relevancy: float
    faithfulness: float
    context_quality: float
    needs_web_search: bool
    explanation: str
    answer: str
    retrieval_confidence: float
    trust_level: str


class RetrievalEvidence(TypedDict):
    query: str
    chunk_id: str
    page: int
    confidence: float
    trust_score: float


class WebSearchEvidence(TypedDict):
    query: str
    source: str
    title: str
    url: str


class Finding(TypedDict):
    severity: str
    file_path: str
    start_line: int
    end_line: int
    regulation_name: str
    jurisdiction: str
    explanation: str
    remedy: str
    rag_chunk_id: str
    rag_page: int


class FileResult(TypedDict):
    file_path: str
    file_type: str
    language: str | None
    status: str
    summary: str
    predicted_output: str | None
    findings: list[Finding]
    report_path: str | None
    error: str | None
    agentic_grade: NotRequired[AgenticGrade | None]
    retrieval_evidence: NotRequired[list[RetrievalEvidence]]
    web_search_evidence: NotRequired[list[WebSearchEvidence]]


class ProgressEvent(TypedDict):
    event_type: str
    file_path: str
    message: str
    timestamp: str


class ComplianceState(TypedDict):
    file_path: str
    file_content: str
    config: dict[str, Any]
    llm_provider: str
    llm_model: str
    opened_workspace_root: NotRequired[str | None]
    restrict_directory_analysis_to_workspace: NotRequired[bool]
    line_offset: NotRequired[int]
    reviewed_context: NotRequired[list[dict[str, Any]]]
    agentic_context: NotRequired[str]
    directory_analysis_path: NotRequired[str | None]
    workspace_root: NotRequired[str | None]
    file_result: FileResult | None
    progress_events: Annotated[list[ProgressEvent], operator.add]
    final_report_md: str | None
    scan_complete: bool
    scan_error: str | None
    langsmith_run_id: str | None
    langsmith_run_url: str | None
