# AI Ethics Compliance Agent

## Product Requirements Document — v3.0

_April 2026 · Status: DRAFT · Priority: P0_

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [System Architecture](#3-system-architecture)
4. [LangGraph Graph Definitions](#4-langgraph-graph-definitions)
5. [Agent & Node Catalogue](#5-agent--node-catalogue)
6. [Tool Catalogue](#6-tool-catalogue)
7. [LLM Provider System](#7-llm-provider-system)
8. [RAG Knowledge Base](#8-rag-knowledge-base)
9. [LangSmith Tracing](#9-langsmith-tracing)
10. [Streamlit UI Specification](#10-streamlit-ui-specification)
11. [Report Specification](#11-report-specification)
12. [Project Directory Structure](#12-project-directory-structure)
13. [Configuration Reference](#13-configuration-reference)
14. [Python Dependencies](#14-python-dependencies)
15. [End-to-End Data Flow](#15-end-to-end-data-flow)
16. [Future Architecture — MCP Server & VS Code Extension](#16-future-architecture--mcp-server--vs-code-extension)
17. [Acceptance Criteria](#17-acceptance-criteria)
18. [Open Questions](#18-open-questions)
19. [Revision History](#19-revision-history)

---

## 1. Executive Summary

The **AI Ethics Compliance Agent** is an autonomous, multi-agent orchestration system built on **LangGraph** that scans any working directory — codebases, document collections, datasets, or mixed-content folders — and produces a comprehensive compliance audit report against the global corpus of AI ethics rules, regulations, and laws.

The system is implemented as a **LangGraph StateGraph** with typed state, conditional routing, persistent checkpointing, and full LangSmith tracing baked in at every node. Each file in the target directory is analysed by specialised graph nodes that reason about code semantics and predicted outputs, document intent, and data source provenance. Violations are matched against a RAG knowledge base and written into per-file analysis reports, culminating in a single consolidated compliance report.

Key architectural choices vs v2.0:

- **All orchestration is a LangGraph graph** — no ad-hoc ThreadPoolExecutor management. LangGraph's `Send` API drives fan-out parallelism across files.
- **State is fully typed** using `TypedDict` with `Annotated` reducer fields — all concurrent writes are safe by construction.
- **Checkpointing** via `SqliteSaver` means interrupted scans can be resumed exactly where they left off.
- **LangSmith** traces every node invocation, every LLM call, every RAG query, and every tool use with rich metadata — giving full observability into what the agent decided and why.
- **Robust filesystem tools** are implemented with retry logic, atomic writes, file locking, and path validation, replacing the thin wrappers of v2.0.

---

## 2. Goals & Non-Goals

### 2.1 Goals

- Autonomously scan all file types (source code, documents, data files, configs) in a target directory.
- Predict the likely output and intent of code files using LLM reasoning _before_ checking compliance.
- Validate data sources (local and remote URLs) referenced inside any scanned file.
- Match detected concerns against a RAG-powered global AI ethics knowledge base built from `ai_ethics_knowledge_base.pdf`.
- Generate per-file `{filename}_analysis_report.md` reports saved under `compliance-analysis/`.
- Generate a consolidated `final_compliance_report.md` and `final_compliance_report.html` report.
- Provide a Streamlit UI with real-time scan progress, report viewer, and LLM provider switcher.
- Support hot-swappable LLM providers (Ollama Cloud, OpenRouter, Groq, Ollama Local) from the UI.
- Provide full **LangSmith observability** for every node, every LLM call, and every tool invocation.
- Support **scan resumption** via LangGraph checkpointing if the process is interrupted.
- Lay the architectural groundwork for an MCP server and VS Code extension without requiring refactoring.

### 2.2 Non-Goals (v1.0)

- Automatic remediation of detected violations (flagging only, not fixing).
- Real-time continuous file-watch mode (batch scan only).
- MCP server or VS Code extension implementation (planned in future milestones).
- Support for compiled binaries without source code.
- Internet-based collection of ethics regulations (the PDF knowledge base is the single source of truth).

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                             │
│   Sidebar: provider/model picker, directory input, start/stop   │
│   Tab 1: Live Scan progress   Tab 2: Report   Tab 3: KB Status  │
│   Tab 4: LangSmith Traces                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ invokes
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              LANGGRAPH COMPLIANCE GRAPH                         │
│  (StateGraph[ComplianceState] with SqliteSaver checkpointer)    │
│                                                                 │
│  START → initialize → fan_out_files → [Send per file] →         │
│         review_file* → [conditional] → validate_data_source* →  │
│         join_results → write_reports → END                      │
│                                                                 │
│  * = nodes that may execute in parallel via LangGraph Send API  │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │  SHARED TOOLS   │
                    │  (ToolNode)     │
                    │  • read_file    │
                    │  • write_file   │
                    │  • list_dir     │
                    │  • run_bash     │
                    │  • query_rag    │
                    │  • web_search   │
                    └─────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │       LANGSMITH             │
              │  • Full trace per graph run │
              │  • Nested spans per node    │
              │  • LLM call logging         │
              │  • Tool call logging        │
              │  • Metadata tags            │
              └─────────────────────────────┘
```

### 3.2 LangGraph State Model

The entire scan state is a single `TypedDict` passed through the graph. LangGraph's reducer annotations make concurrent fan-out writes safe without any manual locking.

```python
# models/state.py
from __future__ import annotations
from typing import Annotated, Any
from typing_extensions import TypedDict
import operator

class Finding(TypedDict):
    severity: str           # HIGH | MEDIUM | LOW
    file_path: str
    start_line: int
    end_line: int
    regulation_name: str
    jurisdiction: str
    explanation: str
    rag_chunk_id: str
    rag_page: int

class DataSourceResult(TypedDict):
    url_or_path: str
    source_type: str        # url | local
    verdict: str            # PASS | WARN | FAIL | SKIPPED
    findings: list[Finding]
    rag_citations: list[str]

class FileResult(TypedDict):
    file_path: str
    file_type: str          # source_code | document | structured_data | config | image_media | binary_unknown
    language: str | None
    status: str             # PASS | WARN | FAIL | ERROR | SKIPPED
    summary: str
    predicted_output: str | None
    findings: list[Finding]
    data_sources: list[DataSourceResult]
    report_path: str | None
    error: str | None

class ProgressEvent(TypedDict):
    event_type: str         # file_started | file_complete | rag_query | data_source_found | violation_found | error
    file_path: str
    message: str
    timestamp: str

class ComplianceState(TypedDict):
    # --- Input (set once at initialize node) ---
    target_directory: str
    config: dict[str, Any]
    llm_provider: str
    llm_model: str

    # --- Discovery (set at fan_out_files node) ---
    all_files: list[str]                              # full list discovered by list_directory
    skipped_files: list[str]                          # filtered out (size, extension)

    # --- Per-file results (reducer: list append — safe for parallel writes) ---
    file_results: Annotated[list[FileResult], operator.add]

    # --- Progress events (reducer: list append — streamed to UI) ---
    progress_events: Annotated[list[ProgressEvent], operator.add]

    # --- Final outputs ---
    final_report_md: str | None
    final_report_html: str | None
    scan_complete: bool
    scan_error: str | None

    # --- LangSmith run metadata ---
    langsmith_run_id: str | None
    langsmith_run_url: str | None
```

**Why this design:**

- `Annotated[list[FileResult], operator.add]` means all parallel `review_file` nodes can write their result concurrently — LangGraph applies the `operator.add` reducer, concatenating lists without data loss or race conditions.
- `progress_events` uses the same reducer pattern so every node can emit events without coordination.
- The state is serialisable to JSON, enabling checkpoint persistence and `ScanResult.to_dict()` for the MCP server milestone.

### 3.3 Design Principles

1. **Entire orchestration is a LangGraph graph.** No ad-hoc thread management in business logic. Parallelism is declared via `Send`, not `ThreadPoolExecutor`.
2. **State is the single source of truth.** No mutable singletons, no shared dicts. Everything lives in `ComplianceState`.
3. **LLM is always injected.** Constructed in `llm/provider_factory.py` and passed into every node at graph construction time via `functools.partial`.
4. **All LLM-calling nodes are `ToolNode`-backed ReAct agents.** Each agent is a `langgraph.prebuilt.create_react_agent` with its designated tool subset and system prompt.
5. **Checkpointing is always on.** `SqliteSaver` is used by default; `PostgresSaver` is supported for production. The graph ID is `compliance-scan-{uuid}` — every scan is replayable.
6. **LangSmith wraps everything.** Every node is decorated with `@traceable`. The graph itself is constructed with `langsmith_extra` metadata. Tool calls and LLM calls are traced as nested child runs.
7. **Filesystem operations are robust.** All file reads/writes use retry logic, file locking, atomic write patterns, and path traversal validation.

---

## 4. LangGraph Graph Definitions

### 4.1 Main Compliance Graph (`graphs/compliance_graph.py`)

```python
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langchain_core.runnables import RunnableConfig

from models.state import ComplianceState
from nodes.initialize import initialize_node
from nodes.fan_out import fan_out_files_node
from nodes.review_file import review_file_node
from nodes.validate_data_source import validate_data_source_node
from nodes.join_results import join_results_node
from nodes.write_reports import write_reports_node
from graphs.checkpointer import get_checkpointer

def should_validate_data_source(state: ComplianceState) -> str:
    """
    Conditional edge: after review_file, check whether the file result
    contains any unvalidated data sources.
    """
    # The last completed file result is identified by examining the most
    # recently appended item in file_results.
    # Note: This edge is evaluated per-Send invocation, scoped to the subgraph.
    return "validate_data_source" if state.get("_pending_data_sources") else "join_results"

def build_compliance_graph() -> StateGraph:
    builder = StateGraph(ComplianceState)

    # ── Nodes ──────────────────────────────────────────────────────────
    builder.add_node("initialize",            initialize_node)
    builder.add_node("fan_out_files",         fan_out_files_node)
    builder.add_node("review_file",           review_file_node)
    builder.add_node("validate_data_source",  validate_data_source_node)
    builder.add_node("join_results",          join_results_node)
    builder.add_node("write_reports",         write_reports_node)

    # ── Edges ──────────────────────────────────────────────────────────
    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "fan_out_files")

    # fan_out_files uses Send API to spawn one review_file invocation per file
    builder.add_conditional_edges(
        "fan_out_files",
        lambda state: [
            Send("review_file", {**state, "_current_file": fp})
            for fp in state["all_files"]
        ],
    )

    # After reviewing, conditionally validate data sources found in the file
    builder.add_conditional_edges(
        "review_file",
        should_validate_data_source,
        {
            "validate_data_source": "validate_data_source",
            "join_results":         "join_results",
        },
    )

    builder.add_edge("validate_data_source", "join_results")

    # join_results waits for ALL fan-out branches (LangGraph handles the barrier)
    builder.add_edge("join_results", "write_reports")
    builder.add_edge("write_reports", END)

    return builder

def compile_graph(checkpointer=None):
    """
    Compile the graph with an optional checkpointer.
    Always use SqliteSaver by default for resumability.
    """
    builder = build_compliance_graph()
    cp = checkpointer or get_checkpointer()
    return builder.compile(checkpointer=cp)
```

### 4.2 Subgraph: File Review ReAct Agent (`graphs/file_review_subgraph.py`)

Each `review_file` node is itself a compiled `create_react_agent` subgraph. This gives us structured tool call/response cycles with automatic retry on tool errors, without custom looping logic.

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from tools.filesystem_tools import read_file_tool, write_file_tool, run_bash_tool
from tools.rag_tool import query_rag_tool
from prompts.loader import load_prompt

def build_file_review_agent(llm):
    """
    Returns a compiled ReAct subgraph for single-file review.
    Tools: read_file, write_file, run_bash, query_rag
    """
    tools = [read_file_tool, write_file_tool, run_bash_tool, query_rag_tool]

    system_prompt = load_prompt("file_reviewer")

    return create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SystemMessage(content=system_prompt),
        # Interrupt before tool execution for human-in-the-loop (future milestone)
        # interrupt_before=["tools"],
    )
```

### 4.3 Subgraph: Data Source Validator ReAct Agent (`graphs/data_validator_subgraph.py`)

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from tools.filesystem_tools import read_file_tool
from tools.rag_tool import query_rag_tool
from tools.web_search_tool import web_search_tool
from prompts.loader import load_prompt

def build_data_validator_agent(llm):
    tools = [read_file_tool, query_rag_tool, web_search_tool]
    system_prompt = load_prompt("data_source_validator")
    return create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=SystemMessage(content=system_prompt),
    )
```

### 4.4 Checkpointer Factory (`graphs/checkpointer.py`)

```python
import os
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver  # optional

CHECKPOINT_DB = os.getenv("CHECKPOINT_DB_PATH", ".langgraph_checkpoints.db")

def get_checkpointer():
    """
    Returns SqliteSaver by default. Switch to PostgresSaver by setting
    CHECKPOINT_BACKEND=postgres and POSTGRES_URI in the environment.
    """
    backend = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    if backend == "postgres":
        uri = os.getenv("POSTGRES_URI")
        if not uri:
            raise EnvironmentError("POSTGRES_URI must be set when CHECKPOINT_BACKEND=postgres")
        return PostgresSaver.from_conn_string(uri)
    return SqliteSaver.from_conn_string(CHECKPOINT_DB)
```

### 4.5 Thread Config & Resumption

Every scan run uses a unique `thread_id`. If a scan is interrupted, it can be resumed by passing the same `thread_id`:

```python
import uuid

# In app.py — starting a new scan
thread_id = str(uuid.uuid4())
st.session_state.scan_thread_id = thread_id

config = RunnableConfig(
    configurable={"thread_id": thread_id},
    tags=["compliance-scan", f"dir:{target_dir}"],
    metadata={
        "target_directory": target_dir,
        "llm_provider": provider,
        "llm_model": model,
        "scan_id": thread_id,
    },
    callbacks=[langsmith_tracer],  # see Section 9
)

# Resume an interrupted scan (same thread_id, graph re-reads from checkpoint)
# graph.invoke(None, config=config)  # passing None resumes from last checkpoint
```

---

## 5. Agent & Node Catalogue

> Each node corresponds to a step in the `ComplianceState` graph. ReAct agent nodes are backed by `create_react_agent` subgraphs. Pure-logic nodes are plain Python functions that transform state.

| Node                   | Type        | Prompt File                        | Parallel?                           | Tools                                              |
| ---------------------- | ----------- | ---------------------------------- | ----------------------------------- | -------------------------------------------------- |
| `initialize`           | Pure Python | —                                  | No                                  | —                                                  |
| `fan_out_files`        | Pure Python | —                                  | No                                  | `list_directory` (direct call)                     |
| `review_file`          | ReAct Agent | `prompts/file_reviewer.md`         | Yes (via Send)                      | `read_file`, `write_file`, `run_bash`, `query_rag` |
| `validate_data_source` | ReAct Agent | `prompts/data_source_validator.md` | No (sequential per Reviewer branch) | `read_file`, `web_search`, `query_rag`             |
| `join_results`         | Pure Python | —                                  | No (barrier)                        | —                                                  |
| `write_reports`        | ReAct Agent | `prompts/report_writer.md`         | No                                  | `write_file`, `read_file`, `run_bash`              |

### 5.1 `initialize` Node (`nodes/initialize.py`)

**Purpose:** Validate inputs, create output directory, emit initial progress event.

```python
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import safe_mkdir
from datetime import datetime, timezone

@traceable(name="initialize", tags=["compliance-scan", "setup"])
def initialize_node(state: ComplianceState) -> dict:
    target = state["target_directory"]
    config = state["config"]

    # Validate target directory exists
    if not os.path.isdir(target):
        return {"scan_error": f"Target directory does not exist: {target}"}

    # Create output directory
    output_dir = os.path.join(target, config["scan"]["output_dir"])
    safe_mkdir(output_dir)

    event = ProgressEvent(
        event_type="scan_started",
        file_path="",
        message=f"Scan initialised. Target: {target}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"progress_events": [event]}
```

### 5.2 `fan_out_files` Node (`nodes/fan_out.py`)

**Purpose:** Discover all files, filter them, categorise them, prepare Send payloads.

```python
from langsmith import traceable
from models.state import ComplianceState
from tools.filesystem_tools import list_directory_robust
import python_magic

SKIP_EXTENSIONS = set()  # loaded from config

@traceable(name="fan_out_files", tags=["compliance-scan", "discovery"])
def fan_out_files_node(state: ComplianceState) -> dict:
    config  = state["config"]
    skip_ext = set(config["scan"]["skip_extensions"])
    max_mb   = config["scan"]["max_file_size_mb"]

    all_paths = list_directory_robust(state["target_directory"], recursive=True)

    accepted, skipped = [], []
    for fp in all_paths:
        ext  = os.path.splitext(fp)[1].lower()
        size = os.path.getsize(fp) / (1024 * 1024)
        if ext in skip_ext or size > max_mb:
            skipped.append(fp)
        else:
            accepted.append(fp)

    event = ProgressEvent(
        event_type="discovery_complete",
        file_path="",
        message=f"Discovered {len(accepted)} files to scan, {len(skipped)} skipped.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "all_files":       accepted,
        "skipped_files":   skipped,
        "progress_events": [event],
    }
```

**Note:** The conditional edge from `fan_out_files` returns a list of `Send("review_file", {...})` objects — one per accepted file. LangGraph executes all of them in parallel (bounded by the runtime's thread pool, configurable via `max_concurrency` in `RunnableConfig`).

### 5.3 `review_file` Node (`nodes/review_file.py`)

**Purpose:** Deep per-file analysis via a ReAct agent subgraph. This is the core intelligence of the system.

```python
from langsmith import traceable
from langgraph.prebuilt import create_react_agent
from models.state import ComplianceState, FileResult, ProgressEvent
from graphs.file_review_subgraph import build_file_review_agent
from llm.provider_factory import create_llm
import json

@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState) -> dict:
    file_path = state["_current_file"]
    config    = state["config"]

    # Emit started event
    start_event = ProgressEvent(
        event_type="file_started",
        file_path=file_path,
        message=f"Starting review: {os.path.basename(file_path)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    llm   = create_llm(state["llm_provider"], state["llm_model"])
    agent = build_file_review_agent(llm)

    # Invoke the ReAct subgraph with the file path as the user message
    prompt = f"""
    Analyse the following file for AI ethics compliance violations.
    File path: {file_path}
    Output directory for the analysis report: {os.path.join(state['target_directory'], config['scan']['output_dir'])}

    Follow your system prompt instructions exactly. When done, return a JSON object
    matching the FileResult schema. Enclose the JSON in <RESULT>...</RESULT> tags.
    """

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=RunnableConfig(
                tags=["file-review", os.path.basename(file_path)],
                metadata={"file_path": file_path},
            ),
        )
        # Parse FileResult from the agent's final message
        final_msg = result["messages"][-1].content
        file_result = _parse_file_result(final_msg, file_path)
    except Exception as e:
        file_result = FileResult(
            file_path=file_path, file_type="unknown", language=None,
            status="ERROR", summary="", predicted_output=None,
            findings=[], data_sources=[], report_path=None,
            error=str(e),
        )

    # Check whether data sources were found (drives conditional edge)
    pending_sources = [ds for ds in file_result.get("data_sources", []) if ds["verdict"] == "PENDING"]

    complete_event = ProgressEvent(
        event_type="file_complete",
        file_path=file_path,
        message=f"Completed: {os.path.basename(file_path)} → {file_result['status']} ({len(file_result['findings'])} findings)",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return {
        "file_results":           [file_result],
        "progress_events":        [start_event, complete_event],
        "_pending_data_sources":  pending_sources,
        "_current_file_result":   file_result,
    }
```

### 5.4 `validate_data_source` Node (`nodes/validate_data_source.py`)

**Purpose:** Validate every external URL or local dataset path found by the File Reviewer, using a dedicated ReAct agent.

```python
from langsmith import traceable
from models.state import ComplianceState, DataSourceResult, ProgressEvent

@traceable(name="validate_data_source", tags=["compliance-scan", "data-validation"])
def validate_data_source_node(state: ComplianceState) -> dict:
    pending_sources  = state.get("_pending_data_sources", [])
    current_result   = state.get("_current_file_result", {})

    llm   = create_llm(state["llm_provider"], state["llm_model"])
    agent = build_data_validator_agent(llm)

    validated_sources = []
    events = []
    for source in pending_sources:
        event = ProgressEvent(
            event_type="data_source_found",
            file_path=current_result.get("file_path", ""),
            message=f"Validating data source: {source['url_or_path']}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        events.append(event)

        prompt = f"""
        Validate this data source for AI ethics compliance:
        Source: {source['url_or_path']}
        Source type: {source['source_type']}
        Context: Found in file {current_result.get('file_path', '')}
        Return a JSON DataSourceResult in <RESULT>...</RESULT> tags.
        """
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]},
                                  config=RunnableConfig(tags=["data-validation"]))
            ds_result = _parse_datasource_result(result["messages"][-1].content, source)
        except Exception as e:
            ds_result = DataSourceResult(
                url_or_path=source["url_or_path"], source_type=source["source_type"],
                verdict="SKIPPED", findings=[], rag_citations=[],
            )
        validated_sources.append(ds_result)

    # Merge validated sources back into the existing FileResult for this file
    # The file_results list already has the FileResult appended by review_file;
    # we emit an updated version and the join_results node reconciles.
    updated_result = {**current_result, "data_sources": validated_sources}

    return {
        "file_results":          [updated_result],   # reducer appends; join_results deduplicates by file_path
        "progress_events":       events,
        "_pending_data_sources": [],
    }
```

### 5.5 `join_results` Node (`nodes/join_results.py`)

**Purpose:** Barrier node. De-duplicates `file_results` (the reducer appends from both `review_file` and `validate_data_source`; this node keeps only the most complete version per file path).

```python
from langsmith import traceable
from models.state import ComplianceState

@traceable(name="join_results", tags=["compliance-scan", "aggregation"])
def join_results_node(state: ComplianceState) -> dict:
    # De-duplicate: keep the last (most complete) result per file_path
    seen = {}
    for result in state["file_results"]:
        seen[result["file_path"]] = result
    deduplicated = list(seen.values())

    event = ProgressEvent(
        event_type="aggregation_complete",
        file_path="",
        message=f"All {len(deduplicated)} file results aggregated.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"file_results": deduplicated, "progress_events": [event]}
```

**Note:** The `join_results` node acts as a **fan-in barrier**. LangGraph will not execute this node until every branch spawned by `fan_out_files` has completed (either `review_file` → `join_results` or `review_file` → `validate_data_source` → `join_results`).

### 5.6 `write_reports` Node (`nodes/write_reports.py`)

**Purpose:** Synthesise all `FileResult` objects into final reports via a ReAct agent. Renders both Markdown and HTML.

```python
from langsmith import traceable
from models.state import ComplianceState

@traceable(name="write_reports", tags=["compliance-scan", "reporting"])
def write_reports_node(state: ComplianceState) -> dict:
    llm   = create_llm(state["llm_provider"], state["llm_model"])
    agent = build_report_writer_agent(llm)

    results_json = json.dumps([dict(r) for r in state["file_results"]], indent=2)
    output_dir   = os.path.join(state["target_directory"], state["config"]["scan"]["output_dir"])

    prompt = f"""
    You have the complete scan results for {len(state['file_results'])} files.
    Output directory: {output_dir}
    Results JSON:
    {results_json}

    Write final_compliance_report.md and final_compliance_report.html to the output directory.
    Return paths in <RESULT>{{"md_path": "...", "html_path": "..."}}</RESULT>.
    """

    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]},
                          config=RunnableConfig(tags=["report-writing"]))

    paths  = _parse_report_paths(result["messages"][-1].content)
    md_content   = safe_read_file(paths["md_path"])
    html_content = safe_read_file(paths["html_path"])

    event = ProgressEvent(
        event_type="scan_complete",
        file_path="",
        message="Final compliance reports written.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "final_report_md":   md_content,
        "final_report_html": html_content,
        "scan_complete":     True,
        "progress_events":   [event],
    }
```

---

## 6. Tool Catalogue

| Tool                    | Provided By                 | Available To                                           | Description                                                                                      |
| ----------------------- | --------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `list_directory_robust` | `tools/filesystem_tools.py` | `fan_out_files` (direct), all agents                   | Recursively list files with retry, symlink-safe, returns flat list of absolute paths with sizes. |
| `read_file_tool`        | `tools/filesystem_tools.py` | `review_file`, `validate_data_source`, `write_reports` | Read file with retry, line range support, path traversal guard, encoding detection.              |
| `write_file_tool`       | `tools/filesystem_tools.py` | `review_file`, `write_reports`                         | Atomic write via temp file + rename, creates parent dirs, file locking, path traversal guard.    |
| `run_bash_tool`         | `tools/filesystem_tools.py` | `review_file`, `write_reports`                         | Run shell command with timeout, stdout/stderr capture, non-zero exit raises ToolException.       |
| `web_search_tool`       | `tools/web_search_tool.py`  | `validate_data_source`                                 | Tavily search with DuckDuckGo fallback; wrapped as `@tool` with LangSmith auto-tracing.          |
| `query_rag_tool`        | `tools/rag_tool.py`         | `review_file`, `validate_data_source`                  | Semantic similarity search against ChromaDB; returns top-k chunks with text, metadata, score.    |

### 6.1 Robust Filesystem Tools (`tools/filesystem_tools.py`)

All filesystem operations include: retry with exponential backoff (`tenacity`), path traversal validation, atomic write semantics, and file locking (`filelock`). Every tool is wrapped with `@tool` so LangGraph's `ToolNode` can dispatch it and LangSmith auto-traces it.

```python
import os, stat, tempfile, shutil, subprocess, chardet
from pathlib import Path
from typing import Optional
from langchain.tools import tool
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from filelock import FileLock, Timeout

# ── Path Safety ─────────────────────────────────────────────────────────────

def _safe_path(path: str, allowed_root: Optional[str] = None) -> Path:
    """
    Resolve the path and optionally verify it stays within allowed_root.
    Raises ValueError on path traversal attempts.
    """
    resolved = Path(path).resolve()
    if allowed_root:
        root = Path(allowed_root).resolve()
        if not str(resolved).startswith(str(root)):
            raise ValueError(f"Path traversal detected: {path} escapes {allowed_root}")
    return resolved

# ── list_directory_robust ────────────────────────────────────────────────────

@traceable(name="list_directory_robust")
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4),
       retry=retry_if_exception_type(OSError))
def list_directory_robust(path: str, recursive: bool = True) -> list[dict]:
    """
    Recursively list all files under path.
    Returns: [{"path": str, "size_bytes": int, "is_symlink": bool}, ...]
    Skips unreadable paths, logs warnings. Never follows symlinks outside root.
    """
    root    = _safe_path(path)
    results = []

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    glob_fn = root.rglob("*") if recursive else root.glob("*")
    for p in glob_fn:
        try:
            # Never follow symlinks outside the root
            if p.is_symlink():
                real = p.resolve()
                if not str(real).startswith(str(root)):
                    continue
            if p.is_file():
                results.append({
                    "path":       str(p),
                    "size_bytes": p.stat().st_size,
                    "is_symlink": p.is_symlink(),
                })
        except (PermissionError, OSError):
            pass  # skip unreadable entries silently

    return results

# ── safe_mkdir ────────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2))
def safe_mkdir(path: str) -> None:
    """Create directory and all parents. Idempotent. Thread-safe."""
    Path(path).mkdir(parents=True, exist_ok=True)

# ── read_file_tool ────────────────────────────────────────────────────────────

@tool
@traceable(name="read_file", tags=["filesystem"])
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4),
       retry=retry_if_exception_type(OSError))
def read_file_tool(path: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    Read the content of a file. Optionally specify a line range.
    Handles binary detection, encoding auto-detection, and large-file safety.
    Returns raw text for text files, '<binary file: {mime_type}>' for binary.
    """
    resolved = _safe_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Path is a directory: {path}")

    # Binary check via first 8 KB
    with open(resolved, "rb") as f:
        header = f.read(8192)
    if b"\x00" in header:
        return f"<binary file: {path}>"

    # Encoding detection
    enc_result = chardet.detect(header)
    encoding   = enc_result.get("encoding") or "utf-8"

    with open(resolved, "r", encoding=encoding, errors="replace") as f:
        lines = f.readlines()

    if start_line > 1 or end_line != -1:
        lo = max(0, start_line - 1)
        hi = end_line if end_line != -1 else len(lines)
        lines = lines[lo:hi]

    return "".join(lines)

# ── write_file_tool ───────────────────────────────────────────────────────────

@tool
@traceable(name="write_file", tags=["filesystem"])
def write_file_tool(path: str, content: str) -> str:
    """
    Atomically write content to a file. Creates parent directories automatically.
    Uses a temp file + rename for crash safety. File locking prevents concurrent corruption.
    Returns: "OK: wrote {n} bytes to {path}"
    """
    resolved = _safe_path(path)
    safe_mkdir(str(resolved.parent))

    lock_path = str(resolved) + ".lock"
    try:
        with FileLock(lock_path, timeout=30):
            # Write to a temp file in the same directory, then atomically rename
            fd, tmp_path = tempfile.mkstemp(
                dir=resolved.parent, prefix=f".{resolved.name}.tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                shutil.move(tmp_path, resolved)
            except Exception:
                os.unlink(tmp_path)
                raise
    except Timeout:
        raise RuntimeError(f"Could not acquire write lock for {path} within 30s")

    n = resolved.stat().st_size
    return f"OK: wrote {n} bytes to {path}"

# ── run_bash_tool ─────────────────────────────────────────────────────────────

@tool
@traceable(name="run_bash", tags=["filesystem"])
def run_bash_tool(command: str, timeout: int = 60) -> str:
    """
    Run a shell command. Returns combined stdout+stderr.
    Non-zero exit code raises ToolException with the output included.
    Max timeout: 60 seconds. Command length limit: 1000 characters.
    """
    if len(command) > 1000:
        raise ValueError("Command too long (>1000 chars). Refusing to execute.")

    # Block obviously dangerous patterns
    BANNED = ["rm -rf /", "dd if=", "> /dev/sda", "mkfs"]
    for pattern in BANNED:
        if pattern in command:
            raise ValueError(f"Dangerous command pattern detected: {pattern}")

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        timeout=timeout, cwd="/tmp",
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        from langchain_core.tools import ToolException
        raise ToolException(f"Command exited {result.returncode}:\n{output}")
    return output
```

### 6.2 RAG Tool (`tools/rag_tool.py`)

```python
from langchain.tools import tool
from langsmith import traceable
from rag.retriever import Retriever

@tool
@traceable(name="query_rag", tags=["rag"])
def query_rag_tool(description: str, top_k: int = 5) -> list[dict]:
    """
    Search the AI ethics knowledge base for regulations relevant to the
    given description. Returns a list of regulation chunks with text and
    source metadata. Always call this before concluding whether a finding
    is a violation.
    """
    retriever = Retriever.get_instance()
    return retriever.query(description, top_k=top_k)
```

### 6.3 Web Search Tool (`tools/web_search_tool.py`)

```python
import os
from langchain.tools import tool
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential

@tool
@traceable(name="web_search", tags=["web"])
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def web_search_tool(query: str, max_results: int = 3) -> list[dict]:
    """
    Search the web for information about a data source, publisher, or URL.
    Falls back to DuckDuckGo if TAVILY_API_KEY is not set.
    """
    if os.getenv("TAVILY_API_KEY"):
        from tavily import TavilyClient
        client  = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query, max_results=max_results)
        return results["results"]
    else:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
```

---

## 7. LLM Provider System

### 7.1 Default Configuration

| Setting            | Value                                                                  |
| ------------------ | ---------------------------------------------------------------------- |
| Default Provider   | `ollama_cloud`                                                         |
| Default Model      | `glm4:cloud`                                                           |
| Fallback behaviour | If provider ping fails, show error in sidebar — do not silently switch |

### 7.2 Supported Providers

| Provider Key   | Display Name             | Suggested Models                                                                    | Auth                   |
| -------------- | ------------------------ | ----------------------------------------------------------------------------------- | ---------------------- |
| `ollama_cloud` | Ollama Cloud _(default)_ | `glm4:cloud`, `llama3.3:cloud`, `qwen2.5:cloud`                                     | `OLLAMA_CLOUD_API_KEY` |
| `openrouter`   | OpenRouter               | `anthropic/claude-3.5-sonnet`, `openai/gpt-4o`, `meta-llama/llama-3.3-70b-instruct` | `OPENROUTER_API_KEY`   |
| `groq`         | Groq                     | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`, `gemma2-9b-it`                     | `GROQ_API_KEY`         |
| `ollama_local` | Ollama Local             | Auto-detected via `ollama list`                                                     | None                   |

### 7.3 Provider Factory (`llm/provider_factory.py`)

LangGraph passes the LLM into nodes via `functools.partial`. The factory is the **only place** provider imports exist. All LLMs are wrapped with a `RateLimiter` and `with_retry` for robustness.

```python
import os, functools
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

def create_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
    rate_limiter = InMemoryRateLimiter(requests_per_second=2, max_bucket_size=10)

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model,
            base_url="https://cloud.ollama.com",
            api_key=os.getenv("OLLAMA_CLOUD_API_KEY"),
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            rate_limiter=rate_limiter,
            **kwargs,
        )
    elif provider == "ollama_local":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            rate_limiter=rate_limiter,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    # Wrap with automatic retry on transient errors (tenacity-based)
    return llm.with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )
```

---

## 8. RAG Knowledge Base

### 8.1 Source Document

- **File:** `ai_ethics_knowledge_base.pdf` — must be placed at the project root by the user.
- **Ingestion:** runs automatically on first launch if `.chroma_db/` does not exist.

### 8.2 Ingestion Pipeline (`rag/ingestor.py`)

```python
import fitz
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langsmith import traceable

CHROMA_PATH = ".chroma_db"
COLLECTION  = "ai_ethics_kb"
PDF_PATH    = "ai_ethics_knowledge_base.pdf"

@traceable(name="rag_ingest", tags=["rag", "setup"])
def ingest():
    doc   = fitz.open(PDF_PATH)
    pages = [{"text": page.get_text(), "page": i+1} for i, page in enumerate(doc)]

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks, metadatas, ids = [], [], []
    for p in pages:
        for j, chunk in enumerate(splitter.split_text(p["text"])):
            cid = f"p{p['page']}_c{j}"
            chunks.append(chunk)
            metadatas.append({"page": p["page"], "source": PDF_PATH, "chunk_id": cid})
            ids.append(cid)

    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectors  = embedder.embed_documents(chunks)

    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION)
    collection.add(documents=chunks, embeddings=vectors, metadatas=metadatas, ids=ids)

    count = collection.count()
    assert count > 0, "Ingestion produced zero chunks."
    print(f"✓ Ingested {count} chunks into ChromaDB")

def needs_ingestion() -> bool:
    try:
        client     = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION)
        return collection.count() == 0
    except Exception:
        return True
```

### 8.3 Retriever (`rag/retriever.py`)

```python
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langsmith import traceable

class Retriever:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.embedder   = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        client          = chromadb.PersistentClient(path=".chroma_db")
        self.collection = client.get_collection("ai_ethics_kb")

    @traceable(name="rag_query", tags=["rag"])
    def query(self, description: str, top_k: int = 5) -> list[dict]:
        vector  = self.embedder.embed_query(description)
        results = self.collection.query(query_embeddings=[vector], n_results=top_k)
        chunks  = []
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "text":     doc,
                "metadata": results["metadatas"][0][i],
                "score":    results["distances"][0][i],
            })
        return chunks
```

---

## 9. LangSmith Tracing

LangSmith is a first-class requirement in v3.0. Every meaningful operation — graph node execution, LLM call, tool invocation, RAG query — must appear as a named span in LangSmith with rich metadata. This provides full observability into what the agents decided and why, enabling debugging of false positives, missed violations, and LLM reasoning failures.

### 9.1 Environment Setup

```bash
# .env.example (new entries for LangSmith)
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # default
LANGSMITH_TRACING_V2=true
```

LangSmith tracing activates automatically when `LANGSMITH_TRACING_V2=true` is set. All LangChain and LangGraph calls are traced without additional code changes. Explicit `@traceable` decorators are added for pure-Python nodes and custom functions to ensure 100% coverage.

### 9.2 Graph-Level Tracing (`tracing/langsmith_setup.py`)

```python
import os
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer
from langchain_core.tracers.context import tracing_v2_enabled

LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")

def get_langsmith_tracer(run_name: str, tags: list[str] = None) -> LangChainTracer:
    """
    Returns a LangChainTracer that logs all events to the LangSmith project.
    Pass this as a callback in RunnableConfig.
    """
    return LangChainTracer(
        project_name=LANGSMITH_PROJECT,
        example_id=None,
    )

def get_run_config(thread_id: str, target_dir: str, provider: str, model: str) -> dict:
    """
    Returns the full RunnableConfig for a scan run.
    Includes tracing callbacks, tags, and metadata.
    """
    tracer = get_langsmith_tracer(run_name=f"scan-{thread_id}")
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks":    [tracer],
        "tags":         [
            "compliance-scan",
            f"provider:{provider}",
            f"model:{model}",
        ],
        "metadata": {
            "thread_id":        thread_id,
            "target_directory": target_dir,
            "llm_provider":     provider,
            "llm_model":        model,
        },
        "run_name": f"ComplianceScan-{thread_id[:8]}",
    }
```

### 9.3 Per-Node Tracing Conventions

Every node function is decorated with `@traceable`. The decorator adds the node's span as a child of the parent graph run, preserving the full call hierarchy in LangSmith.

```python
# Example: how @traceable is applied to a node
from langsmith import traceable

@traceable(
    name="review_file",           # Span name visible in LangSmith UI
    tags=["compliance-scan", "file-review"],
    metadata_func=lambda inputs, outputs: {  # Dynamic metadata from inputs/outputs
        "file_path":     inputs.get("_current_file", ""),
        "status":        outputs.get("file_results", [{}])[-1].get("status", ""),
        "findings_count": len(outputs.get("file_results", [{}])[-1].get("findings", [])),
    },
)
def review_file_node(state: ComplianceState) -> dict:
    ...
```

Naming conventions for LangSmith spans:

| Span Name                       | Description                              |
| ------------------------------- | ---------------------------------------- |
| `ComplianceScan-{id[:8]}`       | Top-level graph run                      |
| `initialize`                    | Initialization node                      |
| `fan_out_files`                 | File discovery node                      |
| `review_file:{basename}`        | Per-file ReAct agent run                 |
| `validate_data_source:{source}` | Per-source validation run                |
| `join_results`                  | Aggregation barrier                      |
| `write_reports`                 | Final report writer                      |
| `rag_query:{description[:50]}`  | RAG retrieval call                       |
| `read_file:{path}`              | File read operation                      |
| `write_file:{path}`             | File write operation                     |
| `web_search:{query[:50]}`       | Web search call                          |
| `llm_call:{node}`               | LLM invocation (auto-named by LangChain) |

### 9.4 LangSmith Dataset & Evaluation (Future)

The tracing setup is designed to feed LangSmith's evaluation framework. Once traces are accumulated:

1. **Annotate traces** in the LangSmith UI — mark findings as true/false positives.
2. **Create a dataset** from annotated traces for regression testing.
3. **Run evaluators** via `langsmith.evaluate()` to measure precision/recall of the compliance agent against known-violation test files.

This is not implemented in v1.0 but the `@traceable` decorators and metadata fields make it straightforward.

### 9.5 LangSmith UI Tab in Streamlit

Tab 4 of the Streamlit UI shows the LangSmith trace for the current scan:

```python
# ui/langsmith_tab.py
import streamlit as st
from langsmith import Client

def render_langsmith_tab():
    run_id  = st.session_state.get("langsmith_run_id")
    run_url = st.session_state.get("langsmith_run_url")

    if not run_id:
        st.info("No scan has run yet. LangSmith traces will appear here after a scan.")
        return

    st.markdown(f"**LangSmith Run:** [{run_id[:8]}...]({run_url})")
    st.markdown("View the full trace, node-by-node reasoning, tool calls, and LLM inputs/outputs on LangSmith.")

    # Fetch run summary via LangSmith Client
    client = Client()
    try:
        run = client.read_run(run_id)
        st.metric("Total Tokens",    run.total_tokens or "—")
        st.metric("Total LLM Calls", len(list(client.list_runs(run_id=run_id, execution_order=1))) or "—")
        st.metric("Duration (s)",    round((run.end_time - run.start_time).total_seconds(), 1) if run.end_time else "Running")
        st.link_button("Open in LangSmith →", run_url)
    except Exception as e:
        st.warning(f"Could not fetch LangSmith run details: {e}")
```

### 9.6 Trace Metadata Schema

Every graph invocation logs the following metadata to LangSmith, queryable via the LangSmith SDK:

```json
{
  "thread_id": "uuid-of-this-scan",
  "target_directory": "/path/to/scanned/project",
  "llm_provider": "ollama_cloud",
  "llm_model": "glm4:cloud",
  "total_files": 23,
  "pass_count": 14,
  "warn_count": 6,
  "fail_count": 3,
  "error_count": 0,
  "total_findings": 17,
  "rag_chunk_count": 342,
  "scan_duration_s": 187.4
}
```

---

## 10. Streamlit UI Specification

### 10.1 Application Layout

```
┌─── SIDEBAR ─────────────────────────┐  ┌─── MAIN AREA ─────────────────────────────┐
│ 🛡 AI Ethics Compliance Agent        │  │ ┌─────┬──────────┬───────────┬──────────┐ │
│                                     │  │ │ 📡  │  📄       │  🗄        │ 🔍       │ │
│ Target Directory                    │  │ │Live │ Report   │ Knowledge │LangSmith │ │
│ [/path/to/directory         ] [📁]  │  │ │Scan │ Viewer   │ Base      │Traces    │ │
│                                     │  │ └─────┴──────────┴───────────┴──────────┘ │
│ ── LLM Provider ──────────────────  │  │                                           │
│ Provider  [Ollama Cloud        ▼]   │  │  TAB 1 — Live Scan                        │
│ Model     [glm4:cloud          ▼]   │  │  ┌─────────────────────────────┐          │
│ API Key   [••••••••••••••••••  ]    │  │  │ ████████████░░░░  14 / 23   │          │
│ [Test Connection  ✓ Connected  ]    │  │  └─────────────────────────────┘          │
│                                     │  │                                           │
│ ── Settings ───────────────────── ▼ │  │  Filename         Status  Findings        │
│  Max concurrency: [6     ]          │  │  main.py          ✅ PASS     0           │
│  RAG top-k:       [5     ]          │  │  train_model.py   ⚠️ WARN     3           │
│  Max file size:   [50 MB ]          │  │  dataset.csv      🔴 FAIL     7           │
│  Resume scan:     [thread-id ▼]     │  │  config.yaml      ✅ PASS     0           │
│                                     │  │                                           │
│ [    START SCAN    ]                │  │  Live log:                                 │
│ [    STOP          ] (disabled)     │  │  > [14:32:01] Reviewing train_model        │
│ [    RESUME        ] (if checkpoint)│  │  > [14:32:04] RAG query: 5 chunks         │
│                                     │  │  > [14:32:07] Found 3 violations           │
│ ── Status ─────────────────────── ▼ │  │                                           │
│  Scan: IDLE                         │  │                                           │
│  LangSmith: ✓ Connected             │  │                                           │
│  Checkpoint: ✓ SqliteSaver          │  │                                           │
└─────────────────────────────────────┘  └───────────────────────────────────────────┘
```

### 10.2 Scan Streaming via LangGraph `.astream_events()`

The Streamlit UI uses LangGraph's built-in event streaming API instead of a manual queue. This eliminates the `queue.Queue` polling loop from v2.0 and provides richer events including token-level streaming.

```python
# In app.py — streaming loop using LangGraph's astream_events
import asyncio
import streamlit as st
from langgraph.graph import CompiledGraph

async def run_scan_streaming(graph: CompiledGraph, initial_state: dict, config: dict):
    """
    Stream events from the graph and update Streamlit session state.
    Uses LangGraph's astream_events with event_version='v2'.
    """
    async for event in graph.astream_events(initial_state, config=config, version="v2"):
        kind = event["event"]
        name = event.get("name", "")
        data = event.get("data", {})

        if kind == "on_chain_start" and "review_file" in name:
            file_path = data.get("input", {}).get("_current_file", "")
            st.session_state.file_table[file_path] = {
                "status": "SCANNING", "findings": 0
            }

        elif kind == "on_chain_end" and "review_file" in name:
            output = data.get("output", {})
            results = output.get("file_results", [])
            if results:
                r = results[-1]
                st.session_state.file_table[r["file_path"]] = {
                    "status":   r["status"],
                    "findings": len(r["findings"]),
                }

        elif kind == "on_tool_start":
            st.session_state.log_lines.append(
                f"[{_now()}] Tool: {name} started"
            )

        elif kind == "on_tool_end":
            st.session_state.log_lines.append(
                f"[{_now()}] Tool: {name} complete"
            )

        # Yield control back to Streamlit every event
        await asyncio.sleep(0)
```

### 10.3 Resume Scan Feature

The sidebar shows a **[RESUME]** button when `SqliteSaver` contains a prior incomplete scan. Users can select a previous `thread_id` from a dropdown and resume exactly where the scan stopped:

```python
# Resume: invoke with None state and the existing thread_id config
graph.invoke(None, config={"configurable": {"thread_id": selected_thread_id}})
```

### 10.4 Tab 4 — LangSmith Traces

See Section 9.5.

### 10.5 Error Handling

- LLM call failures: handled by `llm.with_retry()` (3 attempts, exponential jitter). After 3 failures, LangGraph marks the node as errored in the checkpoint and continues other branches.
- Node exceptions: LangGraph catches exceptions in parallel branches; they do not kill the entire graph. The file is marked `ERROR` in state.
- Interrupted scan: checkpoint preserves all completed node outputs. Resume skips completed nodes automatically.
- Missing API key: `st.warning` in sidebar; START button disabled until required key is set.
- Missing `ai_ethics_knowledge_base.pdf`: `st.error` at startup; scan blocked.
- Tavily quota exceeded: `web_search_tool` falls back to DuckDuckGo silently (no exception propagates).

---

## 11. Report Specification

_(Unchanged from v2.0 — same per-file and consolidated report schemas. Refer to Section 9 of PRD v2.0 for the full Markdown templates.)_

The only change: the `write_reports` node now receives a fully typed `ComplianceState` object (not raw text), making the data-to-report rendering more reliable. The Jinja2 HTML template is retained.

---

## 12. Project Directory Structure

```
ai-ethics-compliance-agent/
│
├── app.py                          # Streamlit entry point — UI only, no business logic
├── config.yaml                     # Default configuration
├── .env.example                    # Template for all required API keys (including LangSmith)
├── requirements.txt
├── README.md
│
├── ai_ethics_knowledge_base.pdf    # User-supplied — MUST exist at project root
│
├── graphs/
│   ├── __init__.py
│   ├── compliance_graph.py         # Main StateGraph definition and compile_graph()
│   ├── file_review_subgraph.py     # create_react_agent subgraph for file review
│   ├── data_validator_subgraph.py  # create_react_agent subgraph for data validation
│   ├── report_writer_subgraph.py   # create_react_agent subgraph for report writing
│   └── checkpointer.py             # SqliteSaver / PostgresSaver factory
│
├── nodes/
│   ├── __init__.py
│   ├── initialize.py               # initialize node
│   ├── fan_out.py                  # fan_out_files node (returns Send objects)
│   ├── review_file.py              # review_file node (invokes file_review subgraph)
│   ├── validate_data_source.py     # validate_data_source node
│   ├── join_results.py             # join_results barrier node
│   └── write_reports.py            # write_reports node (invokes report_writer subgraph)
│
├── tools/
│   ├── __init__.py
│   ├── filesystem_tools.py         # Robust read_file, write_file, run_bash, list_directory
│   ├── rag_tool.py                 # query_rag LangChain Tool
│   └── web_search_tool.py          # web_search Tool (Tavily + DuckDuckGo fallback)
│
├── rag/
│   ├── __init__.py
│   ├── ingestor.py                 # PDF → chunks → embeddings → ChromaDB
│   └── retriever.py                # Retriever singleton
│
├── llm/
│   ├── __init__.py
│   └── provider_factory.py         # Unified LLM instantiation with retry + rate limiting
│
├── models/
│   ├── __init__.py
│   ├── state.py                    # ComplianceState TypedDict, FileResult, Finding, etc.
│   └── events.py                   # ProgressEvent TypedDict
│
├── tracing/
│   ├── __init__.py
│   └── langsmith_setup.py          # LangSmith tracer factory, run config builder
│
├── ui/
│   ├── __init__.py
│   ├── sidebar.py                  # Streamlit sidebar: directory input, LLM selector
│   ├── scan_tab.py                 # Tab 1: live progress table + log stream
│   ├── report_tab.py               # Tab 2: HTML report viewer + download buttons
│   ├── kb_tab.py                   # Tab 3: RAG status + debug search
│   └── langsmith_tab.py            # Tab 4: LangSmith run summary + link
│
├── templates/
│   └── report.html.j2              # Jinja2 HTML template for final_compliance_report.html
│
├── prompts/
│   ├── loader.py                   # load_prompt(name) → reads from prompts/{name}.md
│   ├── file_reviewer.md
│   ├── data_source_validator.md
│   └── report_writer.md
│
├── .chroma_db/                     # Persisted ChromaDB vector store (gitignored)
└── .langgraph_checkpoints.db       # SqliteSaver checkpoint DB (gitignored)
```

---

## 13. Configuration Reference

**`config.yaml`:**

```yaml
llm:
  default_provider: ollama_cloud
  default_model: glm4:cloud
  max_retries: 3
  retry_backoff_jitter: true
  rate_limit_rps: 2 # requests per second per LLM instance
  rate_limit_burst: 10

  providers:
    ollama_cloud:
      base_url: https://cloud.ollama.com
      models: [glm4:cloud, llama3.3:cloud, qwen2.5:cloud]
    openrouter:
      base_url: https://openrouter.ai/api/v1
      models:
        - anthropic/claude-3.5-sonnet
        - openai/gpt-4o
        - meta-llama/llama-3.3-70b-instruct
    groq:
      models: [llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it]
    ollama_local:
      base_url: http://localhost:11434
      models: [] # populated dynamically via `ollama list`

rag:
  knowledge_base_pdf: ai_ethics_knowledge_base.pdf
  chroma_persist_dir: .chroma_db
  collection_name: ai_ethics_kb
  chunk_size: 800
  chunk_overlap: 100
  top_k: 5
  embedding_model: all-MiniLM-L6-v2

scan:
  max_concurrency: 6 # LangGraph RunnableConfig max_concurrency
  output_dir: compliance-analysis
  max_file_size_mb: 50
  skip_extensions:
    - .png
    - .jpg
    - .jpeg
    - .gif
    - .bmp
    - .mp4
    - .mp3
    - .zip
    - .tar
    - .gz
    - .whl
    - .pyc

filesystem:
  write_lock_timeout_s: 30 # Max seconds to wait for file write lock
  read_retry_attempts: 3
  read_retry_min_wait_s: 0.5
  read_retry_max_wait_s: 4.0
  bash_timeout_s: 60 # Max seconds for run_bash commands
  bash_max_command_length: 1000

checkpoint:
  backend: sqlite # sqlite | postgres
  sqlite_path: .langgraph_checkpoints.db
  postgres_uri_env: POSTGRES_URI # env var name to read Postgres URI from

web_search:
  tavily_max_results: 3
  fallback_provider: duckduckgo
  retry_attempts: 3

langsmith:
  project: ai-ethics-compliance-agent
  endpoint: https://api.smith.langchain.com
  tracing_v2: true
```

**`.env.example`:**

```
# LLM Providers
OLLAMA_CLOUD_API_KEY=your_ollama_cloud_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
GROQ_API_KEY=your_groq_key_here

# Web Search
TAVILY_API_KEY=your_tavily_key_here  # optional — DuckDuckGo used as fallback

# LangSmith Tracing (required for full observability)
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true

# Checkpoint Backend (optional — sqlite used by default)
CHECKPOINT_BACKEND=sqlite
CHECKPOINT_DB_PATH=.langgraph_checkpoints.db
# POSTGRES_URI=postgresql://user:password@localhost:5432/compliance_checkpoints
```

---

## 14. Python Dependencies

**`requirements.txt`:**

```
# LangGraph + LangChain Core
langgraph>=0.2.0
langgraph-checkpoint-sqlite>=0.1.0
langgraph-checkpoint-postgres>=0.1.0  # optional, for production
langchain>=0.2.0
langchain-community>=0.2.0
langchain-core>=0.2.0

# LLM Providers
langchain-ollama>=0.1.0
langchain-openai>=0.1.0          # also used for OpenRouter
langchain-groq>=0.1.0

# LangSmith
langsmith>=0.1.0

# RAG
chromadb>=0.5.0
sentence-transformers>=3.0.0
PyMuPDF>=1.24.0

# Web Search
tavily-python>=0.3.0
duckduckgo-search>=6.0.0

# Filesystem Robustness
filelock>=3.14.0
chardet>=5.2.0
python-magic>=0.4.27

# Data Parsing
pandas>=2.0.0
python-docx>=1.1.0

# Retry Logic
tenacity>=8.2.0

# UI
streamlit>=1.35.0

# Templating
jinja2>=3.1.0

# Config
python-dotenv>=1.0.0
pyyaml>=6.0.0
```

---

## 15. End-to-End Data Flow

```
User
 │
 ├─1─► Opens Streamlit app: `streamlit run app.py`
 │       └─ app.py: check PDF, check ChromaDB, initialise LangSmith tracer
 │          if not ingested → run ingest() with spinner (@traceable)
 │
 ├─2─► Selects LLM provider + model in sidebar
 │       └─ provider_factory.create_llm(provider, model)
 │          [Test Connection] → ping with 1-token prompt
 │
 ├─3─► Enters target directory → clicks [START SCAN]
 │       └─ thread_id = uuid4()
 │          config = get_run_config(thread_id, ...) with LangSmith tracer callback
 │          initial_state = ComplianceState(target_directory=..., ...)
 │          asyncio.run( graph.astream_events(initial_state, config) )
 │
 ├─4─► LangGraph: START → initialize node
 │       └─ @traceable span: "initialize"
 │          validate dir, safe_mkdir(output_dir), emit ProgressEvent
 │          LangSmith: span logged with metadata
 │
 ├─5─► LangGraph: initialize → fan_out_files node
 │       └─ @traceable span: "fan_out_files"
 │          list_directory_robust() with retry
 │          filter by extension + size
 │          return list[Send("review_file", {state + _current_file: fp})]
 │
 ├─6─► LangGraph: fan_out_files → review_file × N (parallel, max_concurrency=6)
 │       └─ For each file:
 │          @traceable span: "review_file:{basename}"
 │          create_react_agent invoked with file_path
 │          ├─ Tool: read_file(@traceable) → file content
 │          ├─ LLM: classify type, predict output, extract summary
 │          ├─ Tool: query_rag(@traceable) → top-5 regulation chunks
 │          ├─ LLM: reason about violations → list[Finding]
 │          ├─ Tool: write_file(@traceable) → per-file analysis report
 │          └─ append FileResult to state.file_results (operator.add, thread-safe)
 │
 ├─7─► LangGraph: review_file → [conditional]
 │       ├─ if data sources found → validate_data_source node (sequential per branch)
 │       │     @traceable: "validate_data_source:{source}"
 │       │     create_react_agent: web_search + query_rag + read_file
 │       │     append updated FileResult to state.file_results
 │       └─ else → join_results directly
 │
 ├─8─► LangGraph: join_results (barrier — waits for ALL branches)
 │       └─ @traceable: "join_results"
 │          de-duplicate file_results by file_path (keep most complete)
 │
 ├─9─► LangGraph: write_reports node
 │       └─ @traceable: "write_reports"
 │          create_react_agent: synthesise ScanResult → Markdown + HTML
 │          write_file(atomic) → final_compliance_report.md + .html
 │          state.scan_complete = True
 │          LangSmith: top-level span closed, summary metadata written
 │
 ├─10► Streamlit: astream_events loop completes
 │       └─ switch active tab to Report Viewer
 │          show LangSmith run link in Tab 4
 │          download buttons enabled
 │
 └─11► User downloads .md or .html report
         (or opens LangSmith to inspect full trace)
```

---

## 16. Future Architecture — MCP Server & VS Code Extension

### 16.1 Why the Architecture Is Already Ready

| Design decision                                             | Enables                                                      |
| ----------------------------------------------------------- | ------------------------------------------------------------ |
| `compile_graph()` returns a compiled `CompiledStateGraph`   | MCP server calls `graph.invoke(state, config)` directly      |
| `ComplianceState` is a `TypedDict` (JSON-serialisable)      | `ScanResult.to_dict()` works without changes                 |
| `SqliteSaver` checkpointing                                 | MCP server can resume interrupted scans across sessions      |
| LangSmith traces already contain line numbers and reasoning | VS Code extension reads LangSmith API for inline diagnostics |
| `Finding.start_line / end_line` in every result             | VS Code Diagnostic objects map directly                      |
| Prompts in `prompts/` folder, not hardcoded                 | MCP server can inject custom prompts per workspace           |

### 16.2 MCP Server (Milestone 2)

```python
# mcp_server.py  (future — do not implement in v1.0)
from mcp import MCPServer, tool
from graphs.compliance_graph import compile_graph
from tracing.langsmith_setup import get_run_config
import uuid

server = MCPServer(name="ai-ethics-compliance-agent")

@server.tool()
def run_compliance_scan(directory: str, provider: str = "ollama_cloud",
                        model: str = "glm4:cloud") -> dict:
    """Run an AI ethics compliance scan on the given directory."""
    graph     = compile_graph()
    thread_id = str(uuid.uuid4())
    config    = get_run_config(thread_id, directory, provider, model)
    initial   = {"target_directory": directory, "llm_provider": provider,
                 "llm_model": model, "config": load_config()}
    result    = graph.invoke(initial, config=config)
    return ComplianceState_to_dict(result)

if __name__ == "__main__":
    server.run(transport="stdio")
```

### 16.3 VS Code Extension (Milestone 3)

- Communicates with the MCP server over `stdio`.
- Streams LangGraph `astream_events` to update the VS Code webview in real-time.
- `Finding.file_section` maps directly to VS Code Diagnostic objects.
- Severity: `HIGH` → Error (red squiggle), `MEDIUM` → Warning (yellow), `LOW` → Info (blue).
- LangSmith run URL is embedded in the webview for one-click trace inspection.

### 16.4 Architecture Rules to Maintain in v1.0

1. All business logic stays in `graphs/`, `nodes/`, `tools/`, `rag/`, `llm/` — never in `app.py` or `ui/`.
2. `app.py` calls `compile_graph()`, invokes via `astream_events`, and reads state. Nothing else.
3. Every `Finding` must include `file_path`, `start_line`, `end_line`.
4. `ComplianceState` must be fully JSON-serialisable at all times.
5. All `@traceable` decorators must remain — they power the MCP server's observability.

---

## 17. Acceptance Criteria

| ID    | Criterion                                                                                       | Verification                                                 |
| ----- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| AC-01 | App starts without errors when `ai_ethics_knowledge_base.pdf` is present                        | `streamlit run app.py` → no crash                            |
| AC-02 | RAG auto-ingested on first run; chunk count > 0 shown in KB tab                                 | KB tab shows non-zero count                                  |
| AC-03 | Re-ingest button in KB tab clears and rebuilds ChromaDB                                         | Count resets then increases                                  |
| AC-04 | All 4 LLM providers selectable from sidebar without app restart                                 | Dropdown works; ping succeeds                                |
| AC-05 | Scanning a 10-file mixed directory completes in < 5 min on Ollama Cloud default                 | Timed test run                                               |
| AC-06 | Per-file report created for every non-skipped file in `compliance-analysis/`                    | `ls compliance-analysis/`                                    |
| AC-07 | Final `.md` and `.html` reports are generated and non-empty                                     | File existence + size check                                  |
| AC-08 | At least one known violation in a seeded test file is correctly identified with regulation name | Manual review                                                |
| AC-09 | Data Source Validator fires for every HTTP URL found in scanned files                           | LangSmith trace shows `validate_data_source` span            |
| AC-10 | Progress table updates in real-time via `astream_events` without page refresh                   | Visual observation during scan                               |
| AC-11 | Binary/image files are gracefully skipped with status `SKIPPED`                                 | No crash; SKIPPED row in final report                        |
| AC-12 | LLM retry logic fires on transient failure; node not marked ERROR until 3 attempts exhausted    | Simulated failure; LangSmith trace shows retries             |
| AC-13 | Missing `TAVILY_API_KEY` falls back to DuckDuckGo without crashing                              | Remove key; run scan with URL in a file                      |
| AC-14 | `ComplianceState` is JSON-serialisable (`json.dumps(state)` passes)                             | Automated test                                               |
| AC-15 | LangSmith trace is created for every scan and visible in LangSmith UI                           | Open LangSmith after scan                                    |
| AC-16 | Every node appears as a named child span in the LangSmith trace                                 | Visual inspection in LangSmith                               |
| AC-17 | Interrupted scan can be resumed from checkpoint without re-scanning completed files             | Kill process mid-scan; re-run with same thread_id            |
| AC-18 | Concurrent file reviews do not corrupt `file_results` state                                     | Run with 20+ files; verify no duplicates or missing results  |
| AC-19 | Atomic file writes succeed even if two nodes write simultaneously (no partial files)            | Concurrent write stress test                                 |
| AC-20 | Path traversal attack in file path input is rejected by `_safe_path()`                          | Unit test: `read_file("../../etc/passwd")` raises ValueError |

---

## 18. Open Questions

| #    | Question                                                                                   | Recommendation                                                                                                              |
| ---- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| OQ-1 | What is the max context window of `glm4:cloud`?                                            | Check Ollama Cloud docs. If < 8K tokens, implement line-range chunking in read_file calls within the Reviewer.              |
| OQ-2 | Should `compliance-analysis/` be created inside the target directory or the project root?  | Inside the target directory — keeps outputs co-located.                                                                     |
| OQ-3 | Should image files be OCR'd (pytesseract) to check for text?                               | Recommended for v1.1. Skip in v1.0; mark as SKIPPED.                                                                        |
| OQ-4 | Should the final HTML report be self-contained (inline CSS/JS)?                            | Yes — makes it portable and safe for the VS Code webview.                                                                   |
| OQ-5 | LangGraph `Send` fan-out: what happens if `all_files` is empty?                            | `fan_out_files` should detect this and route directly to `write_reports` with an empty-scan result. Add a conditional edge. |
| OQ-6 | Should `SqliteSaver` be WAL-mode for better concurrent write performance?                  | Yes — set `PRAGMA journal_mode=WAL` on the SQLite connection at startup.                                                    |
| OQ-7 | Should LangSmith tracing be optional (graceful degradation if `LANGSMITH_API_KEY` absent)? | Yes — if key is absent, skip tracer callback. All `@traceable` decorators are no-ops without the key.                       |

---
