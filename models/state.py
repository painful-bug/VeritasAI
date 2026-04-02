from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import NotRequired, TypedDict


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
    line_offset: NotRequired[int]
    reviewed_context: NotRequired[list[dict[str, Any]]]
    file_result: FileResult | None
    progress_events: Annotated[list[ProgressEvent], operator.add]
    final_report_md: str | None
    scan_complete: bool
    scan_error: str | None
    langsmith_run_id: str | None
    langsmith_run_url: str | None
