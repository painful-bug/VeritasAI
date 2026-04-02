from __future__ import annotations

import operator
from typing import Annotated, Any

from typing_extensions import NotRequired, TypedDict


class Finding(TypedDict):
    id: str
    title: str
    severity: str
    file_path: str
    start_line: int | None
    end_line: int | None
    section_desc: str
    regulations: list[str]
    jurisdictions: list[str]
    explanation: str
    rag_chunk_id: str | None
    rag_page: int | None


class DataSourceResult(TypedDict):
    url_or_path: str
    source_type: str
    verdict: str
    publisher: str | None
    description: str
    sensitive_fields: list[str]
    concerns: list[str]
    regulations: list[str]
    rag_citations: list[dict[str, Any]]
    path_exists: bool | None
    notes: str | None


class FileResult(TypedDict):
    file_path: str
    file_type: str
    language: str | None
    status: str
    summary: str
    predicted_output: str | None
    findings: list[Finding]
    data_sources: list[DataSourceResult]
    report_path: str | None
    error: str | None
    notes: list[str]


class ProgressEvent(TypedDict):
    event_type: str
    file_path: str
    message: str
    timestamp: str
    metadata: NotRequired[dict[str, Any]]


class ComplianceState(TypedDict):
    target_directory: str
    config: dict[str, Any]
    llm_provider: str
    llm_model: str
    all_files: list[str]
    skipped_files: list[str]
    file_categories: dict[str, str]
    file_results: Annotated[list[FileResult], operator.add]
    progress_events: Annotated[list[ProgressEvent], operator.add]
    final_report_md: str | None
    final_report_html: str | None
    scan_complete: bool
    scan_error: str | None
    langsmith_run_id: str | None
    langsmith_run_url: str | None
    _current_file: NotRequired[str]
    _current_category: NotRequired[str]
    _pending_data_sources: NotRequired[Annotated[list[dict[str, Any]], operator.add]]
    _current_file_result: NotRequired[Annotated[list[FileResult], operator.add]]
    _analysis_output_dir: NotRequired[str]
    _deduped_file_results: NotRequired[list[FileResult]]
