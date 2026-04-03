# AI Ethics Compliance Agent

## Product Requirements Document — v4.0

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
10. [VS Code Extension Specification](#10-vs-code-extension-specification)
11. [Report Specification](#11-report-specification)
12. [Project Directory Structure](#12-project-directory-structure)
13. [Configuration Reference](#13-configuration-reference)
14. [Python Dependencies](#14-python-dependencies)
15. [End-to-End Data Flow](#15-end-to-end-data-flow)
16. [MCP Server](#16-mcp-server)
17. [Acceptance Criteria](#17-acceptance-criteria)
18. [Open Questions](#18-open-questions)
19. [Revision History](#19-revision-history)

---

## 1. Executive Summary

The **AI Ethics Compliance Agent** is an autonomous, multi-agent orchestration system built on **LangGraph** that analyses code files in real-time and reports AI ethics compliance violations inline in the editor — exactly as a type checker does.

The system ships as a **VS Code Extension** that watches the active document. When the user pauses typing for 5 seconds, the backend LangGraph graph is invoked. Each finding is surfaced as a VS Code Diagnostic (red squiggle + inline gutter marker for FAIL, yellow for WARN, blue for INFO) with a short description and an expandable panel containing remediation guidance.

The compliance logic is implemented as a **LangGraph StateGraph** with typed state, `astream_events` streaming, and full LangSmith tracing. Results flow back to the extension via the MCP server's stdio transport.

Key architectural changes from v3.0:

- **Streamlit UI removed entirely.** The VS Code Extension is the sole user-facing surface.
- **LangGraph graph simplified.** The `validate_data_source` node and its conditional edge are removed. File discovery fan-out is replaced with a single-file, single-invocation flow suited to the editor use-case.
- **Streaming is a first-class requirement.** The graph uses `astream_events(version="v2")` throughout; the MCP server proxies the event stream to the extension's webview.
- **Real-time inline diagnostics.** The extension maps `Finding` objects to `vscode.Diagnostic` entries updated on every stream event.

---

## 2. Goals & Non-Goals

### 2.1 Goals

- Analyse the **active VS Code document** for AI ethics compliance violations in real-time.
- Fire the compliance agent **5 seconds after the last document change** (debounced, not on every keystroke).
- Surface violations as **VS Code Diagnostics** — red gutter markers, squiggles, hover descriptions, and an expandable panel with remediation guidance.
- Match detected concerns against a RAG-powered AI ethics knowledge base built from `ai_ethics_knowledge_base.pdf`.
- Support hot-swappable LLM providers (Ollama Cloud, OpenRouter, Groq, Ollama Local) from VS Code settings.
- Provide full **LangSmith observability** for every node, every LLM call, and every tool invocation.
- Support **scan resumption** via LangGraph checkpointing if the process is interrupted.
- Expose the compliance graph as an **MCP server** over stdio so the VS Code extension communicates with the Python backend without bundling Python in the extension.

### 2.2 Non-Goals (v4.0)

- Streamlit UI (removed).
- Full directory batch scan (single active file only in this milestone).
- Automatic remediation of detected violations (flagging and guidance only).
- Support for compiled binaries without source code.
- Internet-based collection of ethics regulations (the PDF knowledge base is the single source of truth).

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     VS CODE EXTENSION                           │
│                                                                 │
│  onDidChangeTextDocument ──► debounce(5s) ──► invoke MCP tool  │
│                                                                 │
│  astream_events proxy ──► DiagnosticCollection update          │
│  (red/yellow/blue gutter markers + hover panels)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ stdio (MCP)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP SERVER (mcp_server.py)                   │
│  tool: check_file(file_path, content, provider, model)         │
│  proxies astream_events back to extension                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ invokes
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              LANGGRAPH COMPLIANCE GRAPH                         │
│  (StateGraph[ComplianceState] with SqliteSaver checkpointer)   │
│                                                                 │
│  START → initialize → review_file → write_report → END         │
│                                                                 │
│  Streaming: graph.astream_events(version="v2")                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │  SHARED TOOLS   │
                    │  (ToolNode)     │
                    │  • read_file    │
                    │  • write_file   │
                    │  • query_rag    │
                    └─────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │       LANGSMITH             │
              │  • Full trace per run       │
              │  • Nested spans per node    │
              │  • LLM call logging         │
              │  • Tool call logging        │
              └─────────────────────────────┘
```

### 3.2 LangGraph State Model

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
    explanation: str        # short — shown inline in VS Code
    remedy: str             # expanded — shown in hover panel
    rag_chunk_id: str
    rag_page: int

class FileResult(TypedDict):
    file_path: str
    file_type: str          # source_code | document | structured_data | config | binary_unknown
    language: str | None
    status: str             # PASS | WARN | FAIL | ERROR | SKIPPED
    summary: str
    predicted_output: str | None
    findings: list[Finding]
    report_path: str | None
    error: str | None

class ProgressEvent(TypedDict):
    event_type: str         # scan_started | rag_query | violation_found | scan_complete | error
    file_path: str
    message: str
    timestamp: str

class ComplianceState(TypedDict):
    # --- Input ---
    file_path: str
    file_content: str
    config: dict[str, Any]
    llm_provider: str
    llm_model: str

    # --- Results ---
    file_result: FileResult | None

    # --- Progress events (reducer: list append — streamed to extension) ---
    progress_events: Annotated[list[ProgressEvent], operator.add]

    # --- Final outputs ---
    final_report_md: str | None
    scan_complete: bool
    scan_error: str | None

    # --- LangSmith run metadata ---
    langsmith_run_id: str | None
    langsmith_run_url: str | None
```

**Why this design:**

- Single-file invocation — no fan-out, no `Send`, no join barrier. The graph is a simple linear chain suited to the editor use-case.
- `progress_events` uses `operator.add` so every node can emit events that stream to the extension in real-time.
- `Finding.remedy` is a new field (vs v3.0) — the extension expands the hover panel to show it.
- The state remains fully JSON-serialisable for checkpoint persistence and MCP transport.

### 3.3 Design Principles

1. **Graph is a simple linear chain.** No fan-out. No conditional edges. `initialize → review_file → write_report → END`.
2. **Streaming is mandatory.** Every node must yield progress events. The MCP server proxies `astream_events` directly — callers never wait for the full result before seeing partial updates.
3. **State is the single source of truth.** No mutable singletons, no shared dicts.
4. **LLM is always injected.** Constructed in `llm/provider_factory.py` and passed into every node at graph construction time.
5. **Checkpointing is always on.** `SqliteSaver` by default; every run is replayable by `thread_id`.
6. **LangSmith wraps everything.** Every node is `@traceable`. The extension shows the LangSmith run URL in its output panel.

---

## 4. LangGraph Graph Definitions

### 4.1 Main Compliance Graph (`graphs/compliance_graph.py`)

```python
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from models.state import ComplianceState
from nodes.initialize import initialize_node
from nodes.review_file import review_file_node
from nodes.write_report import write_report_node
from graphs.checkpointer import get_checkpointer

def build_compliance_graph() -> StateGraph:
    builder = StateGraph(ComplianceState)

    builder.add_node("initialize",    initialize_node)
    builder.add_node("review_file",   review_file_node)
    builder.add_node("write_report",  write_report_node)

    builder.add_edge(START,          "initialize")
    builder.add_edge("initialize",   "review_file")
    builder.add_edge("review_file",  "write_report")
    builder.add_edge("write_report", END)

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

### 4.2 Streaming Invocation

The MCP server (and any caller) must always use `astream_events` — never `invoke`. This ensures findings stream to the VS Code extension in real-time as the agent discovers them, rather than arriving as a single batch at the end.

```python
# mcp_server.py — streaming invocation pattern
import asyncio
from langgraph.graph import CompiledGraph

async def stream_compliance_check(
    graph: CompiledGraph,
    file_path: str,
    file_content: str,
    provider: str,
    model: str,
    thread_id: str,
) -> AsyncIterator[dict]:
    """
    Stream compliance events for a single file.
    Yields raw astream_events dicts for the MCP server to proxy to the extension.
    """
    initial_state = {
        "file_path":    file_path,
        "file_content": file_content,
        "llm_provider": provider,
        "llm_model":    model,
        "config":       load_config(),
    }
    config = get_run_config(thread_id, file_path, provider, model)

    async for event in graph.astream_events(initial_state, config=config, version="v2"):
        yield event
```

**Event types surfaced to the extension:**

| LangGraph event           | Extension action                                     |
| ------------------------- | ---------------------------------------------------- |
| `on_chain_start` (initialize) | Show spinner in status bar                       |
| `on_chain_start` (review_file) | Update status bar: "Analysing…"                 |
| `on_custom_event` (violation_found) | Immediately update DiagnosticCollection   |
| `on_chain_end` (review_file) | Final DiagnosticCollection flush                 |
| `on_chain_end` (write_report) | Hide spinner; show summary in output panel      |
| `on_chain_error`          | Show error notification; clear spinner               |

### 4.3 File Review ReAct Subgraph (`graphs/file_review_subgraph.py`)

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from tools.filesystem_tools import read_file_tool, write_file_tool
from tools.rag_tool import query_rag_tool
from prompts.loader import load_prompt

def build_file_review_agent(llm):
    """
    Returns a compiled ReAct subgraph for single-file review.
    Tools: read_file, write_file, query_rag
    run_bash removed — not needed for single-file editor context.
    """
    tools = [read_file_tool, write_file_tool, query_rag_tool]
    system_prompt = load_prompt("file_reviewer")
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
    backend = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    if backend == "postgres":
        uri = os.getenv("POSTGRES_URI")
        if not uri:
            raise EnvironmentError("POSTGRES_URI must be set when CHECKPOINT_BACKEND=postgres")
        return PostgresSaver.from_conn_string(uri)
    return SqliteSaver.from_conn_string(CHECKPOINT_DB)
```

### 4.5 Thread Config

```python
import uuid
from tracing.langsmith_setup import get_run_config

# New thread per file check
thread_id = str(uuid.uuid4())
config = get_run_config(thread_id, file_path, provider, model)
```

---

## 5. Agent & Node Catalogue

| Node           | Type        | Prompt File              | Tools                                   |
| -------------- | ----------- | ------------------------ | --------------------------------------- |
| `initialize`   | Pure Python | —                        | —                                       |
| `review_file`  | ReAct Agent | `prompts/file_reviewer.md` | `read_file`, `write_file`, `query_rag` |
| `write_report` | Pure Python | —                        | `write_file` (direct)                   |

### 5.1 `initialize` Node (`nodes/initialize.py`)

**Purpose:** Validate inputs, create output directory, emit initial progress event.

```python
import os
from datetime import datetime, timezone
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import safe_mkdir

@traceable(name="initialize", tags=["compliance-scan", "setup"])
def initialize_node(state: ComplianceState) -> dict:
    config     = state["config"]
    file_path  = state["file_path"]
    output_dir = config["scan"]["output_dir"]
    safe_mkdir(output_dir)

    event = ProgressEvent(
        event_type="scan_started",
        file_path=file_path,
        message=f"Scan initialised for: {os.path.basename(file_path)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"progress_events": [event]}
```

### 5.2 `review_file` Node (`nodes/review_file.py`)

**Purpose:** Deep file analysis via a ReAct agent. Emits `violation_found` custom events as each finding is discovered so the extension can update diagnostics incrementally without waiting for the full result.

```python
import os, json
from datetime import datetime, timezone
from langsmith import traceable
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer

from models.state import ComplianceState, FileResult, ProgressEvent, Finding
from graphs.file_review_subgraph import build_file_review_agent
from llm.provider_factory import create_llm

@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState) -> dict:
    file_path    = state["file_path"]
    file_content = state["file_content"]
    config       = state["config"]

    # stream_writer lets this node emit custom events that astream_events surfaces
    # as on_custom_event — picked up immediately by the VS Code extension
    write_stream = get_stream_writer()

    start_event = ProgressEvent(
        event_type="file_started",
        file_path=file_path,
        message=f"Reviewing: {os.path.basename(file_path)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    write_stream({"type": "progress", "data": start_event})

    llm   = create_llm(state["llm_provider"], state["llm_model"])
    agent = build_file_review_agent(llm)

    prompt = f"""
    Analyse the following file for AI ethics compliance violations.
    File path: {file_path}
    File content:
    {file_content}

    For each violation found, emit it immediately using the pattern described in your
    system prompt before continuing the analysis. When done, return a JSON object
    matching the FileResult schema enclosed in <r>...</r> tags.
    """

    try:
        result    = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=RunnableConfig(
                tags=["file-review", os.path.basename(file_path)],
                metadata={"file_path": file_path},
            ),
        )
        final_msg   = result["messages"][-1].content
        file_result = _parse_file_result(final_msg, file_path)

        # Emit each finding as an individual stream event for incremental diagnostics
        for finding in file_result.get("findings", []):
            write_stream({"type": "violation_found", "data": finding})

    except Exception as e:
        file_result = FileResult(
            file_path=file_path, file_type="unknown", language=None,
            status="ERROR", summary="", predicted_output=None,
            findings=[], report_path=None, error=str(e),
        )

    complete_event = ProgressEvent(
        event_type="file_complete",
        file_path=file_path,
        message=f"Completed: {os.path.basename(file_path)} → {file_result['status']} "
                f"({len(file_result['findings'])} findings)",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return {
        "file_result":     file_result,
        "progress_events": [start_event, complete_event],
    }
```

### 5.3 `write_report` Node (`nodes/write_report.py`)

**Purpose:** Serialise the `FileResult` to a Markdown report on disk. This is a lightweight pure-Python node — no LLM call required.

```python
import os, json
from datetime import datetime, timezone
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import write_file_tool

@traceable(name="write_report", tags=["compliance-scan", "reporting"])
def write_report_node(state: ComplianceState) -> dict:
    result     = state["file_result"]
    if result is None:
        return {"scan_complete": True}

    output_dir  = state["config"]["scan"]["output_dir"]
    base        = os.path.splitext(os.path.basename(result["file_path"]))[0]
    report_path = os.path.join(output_dir, f"{base}_analysis_report.md")

    lines = [
        f"# Compliance Report: {result['file_path']}",
        f"**Status:** {result['status']}  |  **Findings:** {len(result['findings'])}",
        f"**Summary:** {result['summary']}",
        "",
        "## Findings",
    ]
    for i, f in enumerate(result["findings"], 1):
        lines += [
            f"### {i}. [{f['severity']}] {f['regulation_name']}",
            f"**Lines:** {f['start_line']}–{f['end_line']}  |  "
            f"**Jurisdiction:** {f['jurisdiction']}",
            f"**Issue:** {f['explanation']}",
            f"**Remedy:** {f['remedy']}",
            "",
        ]

    write_file_tool(report_path, "\n".join(lines))

    event = ProgressEvent(
        event_type="scan_complete",
        file_path=result["file_path"],
        message=f"Report written to {report_path}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "final_report_md": "\n".join(lines),
        "scan_complete":   True,
        "progress_events": [event],
    }
```

---

## 6. Tool Catalogue

| Tool                    | Provided By                 | Available To              | Description                                                                                      |
| ----------------------- | --------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------ |
| `read_file_tool`        | `tools/filesystem_tools.py` | `review_file`             | Read file with retry, line range support, path traversal guard, encoding detection.              |
| `write_file_tool`       | `tools/filesystem_tools.py` | `review_file`, `write_report` | Atomic write via temp file + rename, creates parent dirs, file locking, path traversal guard. |
| `query_rag_tool`        | `tools/rag_tool.py`         | `review_file`             | Semantic similarity search against ChromaDB; returns top-k chunks with text, metadata, score.    |

`run_bash_tool` and `web_search_tool` are removed from the active tool set in v4.0. The data source validation node has been removed. These tools remain in the codebase but are not wired into the graph.

### 6.1 Robust Filesystem Tools (`tools/filesystem_tools.py`)

All filesystem operations include: retry with exponential backoff (`tenacity`), path traversal validation, atomic write semantics, and file locking (`filelock`).

```python
import os, stat, tempfile, shutil, chardet
from pathlib import Path
from typing import Optional
from langchain.tools import tool
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from filelock import FileLock, Timeout

def _safe_path(path: str, allowed_root: Optional[str] = None) -> Path:
    resolved = Path(path).resolve()
    if allowed_root:
        root = Path(allowed_root).resolve()
        if not str(resolved).startswith(str(root)):
            raise ValueError(f"Path traversal detected: {path} escapes {allowed_root}")
    return resolved

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2))
def safe_mkdir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

@tool
@traceable(name="read_file", tags=["filesystem"])
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4),
       retry=retry_if_exception_type(OSError))
def read_file_tool(path: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    Read the content of a file. Optionally specify a line range.
    Handles binary detection, encoding auto-detection, and large-file safety.
    """
    resolved = _safe_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Path is a directory: {path}")

    with open(resolved, "rb") as f:
        header = f.read(8192)
    if b"\x00" in header:
        return f"<binary file: {path}>"

    enc_result = chardet.detect(header)
    encoding   = enc_result.get("encoding") or "utf-8"

    with open(resolved, "r", encoding=encoding, errors="replace") as f:
        lines = f.readlines()

    if start_line > 1 or end_line != -1:
        lo = max(0, start_line - 1)
        hi = end_line if end_line != -1 else len(lines)
        lines = lines[lo:hi]

    return "".join(lines)

@tool
@traceable(name="write_file", tags=["filesystem"])
def write_file_tool(path: str, content: str) -> str:
    """
    Atomically write content to a file. Creates parent directories automatically.
    Uses temp file + rename for crash safety. File locking prevents concurrent corruption.
    """
    resolved  = _safe_path(path)
    safe_mkdir(str(resolved.parent))
    lock_path = str(resolved) + ".lock"
    try:
        with FileLock(lock_path, timeout=30):
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

---

## 7. LLM Provider System

### 7.1 Default Configuration

| Setting            | Value                                                                  |
| ------------------ | ---------------------------------------------------------------------- |
| Default Provider   | `ollama_cloud`                                                         |
| Default Model      | `glm4:cloud`                                                           |
| Fallback behaviour | If provider ping fails, show error notification — do not silently switch |

### 7.2 Supported Providers

| Provider Key   | Display Name             | Suggested Models                                                                    | Auth                   |
| -------------- | ------------------------ | ----------------------------------------------------------------------------------- | ---------------------- |
| `ollama_cloud` | Ollama Cloud _(default)_ | `glm4:cloud`, `llama3.3:cloud`, `qwen2.5:cloud`                                     | `OLLAMA_CLOUD_API_KEY` |
| `openrouter`   | OpenRouter               | `anthropic/claude-3.5-sonnet`, `openai/gpt-4o`, `meta-llama/llama-3.3-70b-instruct` | `OPENROUTER_API_KEY`   |
| `groq`         | Groq                     | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`, `gemma2-9b-it`                     | `GROQ_API_KEY`         |
| `ollama_local` | Ollama Local             | Auto-detected via `ollama list`                                                     | None                   |

### 7.3 Provider Factory (`llm/provider_factory.py`)

```python
import os
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

def create_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
    rate_limiter = InMemoryRateLimiter(requests_per_second=2, max_bucket_size=10)

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model, base_url="https://cloud.ollama.com",
            api_key=os.getenv("OLLAMA_CLOUD_API_KEY"), rate_limiter=rate_limiter, **kwargs,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model, base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"), rate_limiter=rate_limiter, **kwargs,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=model, api_key=os.getenv("GROQ_API_KEY"),
            rate_limiter=rate_limiter, **kwargs,
        )
    elif provider == "ollama_local":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=model, base_url="http://localhost:11434",
            rate_limiter=rate_limiter, **kwargs,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
```

---

## 8. RAG Knowledge Base

### 8.1 Source Document

- **File:** `ai_ethics_knowledge_base.pdf` — must be placed at the project root.
- **Ingestion:** runs automatically on MCP server startup if `.chroma_db/` does not exist.

### 8.2 Ingestion Pipeline (`rag/ingestor.py`)

```python
import fitz, chromadb
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

### 9.1 Environment Setup

```bash
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true
```

LangSmith tracing activates automatically when `LANGSMITH_TRACING_V2=true` is set.

### 9.2 Graph-Level Tracing (`tracing/langsmith_setup.py`)

```python
import os
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer

LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")

def get_langsmith_tracer(run_name: str) -> LangChainTracer:
    return LangChainTracer(project_name=LANGSMITH_PROJECT)

def get_run_config(thread_id: str, file_path: str, provider: str, model: str) -> dict:
    tracer = get_langsmith_tracer(run_name=f"check-{thread_id}")
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks":    [tracer],
        "tags":         ["compliance-scan", f"provider:{provider}", f"model:{model}"],
        "metadata": {
            "thread_id":    thread_id,
            "file_path":    file_path,
            "llm_provider": provider,
            "llm_model":    model,
        },
        "run_name": f"ComplianceCheck-{thread_id[:8]}",
    }
```

### 9.3 LangSmith Span Naming

| Span Name                      | Description                              |
| ------------------------------ | ---------------------------------------- |
| `ComplianceCheck-{id[:8]}`     | Top-level graph run                      |
| `initialize`                   | Initialization node                      |
| `review_file:{basename}`       | File review ReAct agent run              |
| `write_report`                 | Report serialisation node                |
| `rag_query:{description[:50]}` | RAG retrieval call                       |
| `read_file:{path}`             | File read operation                      |
| `write_file:{path}`            | File write operation                     |
| `llm_call:{node}`              | LLM invocation (auto-named by LangChain) |

---

## 10. VS Code Extension Specification

### 10.1 Overview

The VS Code Extension is the primary user-facing deliverable. It watches the active text editor, debounces document changes, and invokes the Python compliance agent via the MCP server. Findings appear as inline diagnostics — identical in UX to TypeScript errors or ESLint warnings — with severity-coded markers and expandable hover panels showing remediation guidance.

### 10.2 Extension Activation & Lifecycle

```typescript
// extension.ts
import * as vscode from 'vscode';

let diagnosticCollection: vscode.DiagnosticCollection;
let debounceTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('ai-ethics');

    // Watch for document changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
            if (event.document !== vscode.window.activeTextEditor?.document) return;
            scheduleCheck(event.document);
        }),
        // Also check when switching to a new file
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor) scheduleCheck(editor.document);
        }),
    );
}

export function deactivate() {
    diagnosticCollection.dispose();
    if (debounceTimer) clearTimeout(debounceTimer);
}
```

### 10.3 Debounce & Trigger Logic

The agent fires **5 seconds after the last document change**. This matches the mental model of a type checker: it runs when you pause, not on every keystroke.

```typescript
const DEBOUNCE_MS = 5000;

function scheduleCheck(document: vscode.TextDocument) {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runComplianceCheck(document), DEBOUNCE_MS);
}
```

To detect whether the user is still actively writing on the last line (and suppress the check until they stop), combine the document change event with cursor position:

```typescript
function isWritingOnLastLine(editor: vscode.TextEditor): boolean {
    const document   = editor.document;
    const cursorLine = editor.selection.active.line;
    const lastLine   = document.lineCount - 1;
    const lineText   = document.lineAt(cursorLine).text;
    // Only suppress if cursor is on the last line AND the line has content
    return cursorLine === lastLine && lineText.trim().length > 0;
}

function scheduleCheck(document: vscode.TextDocument) {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        const editor = vscode.window.activeTextEditor;
        // If still typing on the last line, push the check back
        if (editor && isWritingOnLastLine(editor)) {
            scheduleCheck(document);
            return;
        }
        runComplianceCheck(document);
    }, DEBOUNCE_MS);
}
```

### 10.4 MCP Communication & Streaming

The extension communicates with the Python MCP server over stdio. Findings stream in via `astream_events` proxied through the MCP tool response, so diagnostics update incrementally as the agent works.

```typescript
import { MCPClient } from '@modelcontextprotocol/sdk/client';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio';

let mcpClient: MCPClient | undefined;

async function getMCPClient(): Promise<MCPClient> {
    if (mcpClient) return mcpClient;

    const config    = vscode.workspace.getConfiguration('aiEthics');
    const pythonPath = config.get<string>('pythonPath', 'python');
    const serverPath = config.get<string>('serverPath', '');

    const transport = new StdioClientTransport({
        command: pythonPath,
        args:    [serverPath],
    });
    mcpClient = new MCPClient({ name: 'ai-ethics-vscode', version: '1.0.0' });
    await mcpClient.connect(transport);
    return mcpClient;
}

async function runComplianceCheck(document: vscode.TextDocument) {
    const client   = await getMCPClient();
    const config   = vscode.workspace.getConfiguration('aiEthics');

    // Clear existing diagnostics for this file before a new check
    diagnosticCollection.set(document.uri, []);
    setStatusBar('$(sync~spin) AI Ethics: Analysing…');

    try {
        // The MCP tool streams events back — each violation_found event
        // triggers an immediate diagnostic update
        const stream = await client.callToolStream('check_file', {
            file_path:    document.fileName,
            file_content: document.getText(),
            provider:     config.get('provider', 'ollama_cloud'),
            model:        config.get('model', 'glm4:cloud'),
        });

        const diagnostics: vscode.Diagnostic[] = [];

        for await (const event of stream) {
            if (event.type === 'violation_found') {
                const diag = findingToDiagnostic(event.data, document);
                diagnostics.push(diag);
                // Flush immediately for real-time feedback
                diagnosticCollection.set(document.uri, [...diagnostics]);
            } else if (event.type === 'scan_complete') {
                setStatusBar('$(shield) AI Ethics: Done');
            }
        }
    } catch (err) {
        vscode.window.showErrorMessage(`AI Ethics check failed: ${err}`);
        setStatusBar('$(error) AI Ethics: Error');
    }
}
```

### 10.5 Finding → Diagnostic Mapping

```typescript
function findingToDiagnostic(
    finding: Finding,
    document: vscode.TextDocument,
): vscode.Diagnostic {
    const startLine = Math.max(0, finding.start_line - 1);  // VS Code is 0-indexed
    const endLine   = Math.max(0, finding.end_line   - 1);
    const range     = new vscode.Range(
        new vscode.Position(startLine, 0),
        new vscode.Position(endLine, document.lineAt(endLine).text.length),
    );

    const severity = finding.severity === 'HIGH'
        ? vscode.DiagnosticSeverity.Error
        : finding.severity === 'MEDIUM'
        ? vscode.DiagnosticSeverity.Warning
        : vscode.DiagnosticSeverity.Information;

    const diagnostic         = new vscode.Diagnostic(range, finding.explanation, severity);
    diagnostic.source        = 'AI Ethics';
    diagnostic.code          = finding.regulation_name;

    // Attach remedy as a related information item — shown in the Problems panel
    // and accessible on hover expand
    diagnostic.relatedInformation = [
        new vscode.DiagnosticRelatedInformation(
            new vscode.Location(document.uri, range),
            `Remedy: ${finding.remedy}`,
        ),
    ];

    return diagnostic;
}
```

### 10.6 Inline UX

The diagnostics integrate with VS Code's native Problems panel and inline rendering:

| Severity | VS Code Behaviour                                       |
| -------- | ------------------------------------------------------- |
| HIGH     | Red squiggle + red gutter icon + `[FAILED]` in Problems |
| MEDIUM   | Yellow squiggle + yellow gutter icon + `[WARN]`         |
| LOW      | Blue underline + info gutter icon + `[INFO]`            |

Hovering the squiggle opens the native VS Code hover card, showing:
1. **Line 1:** `[FAILED] <regulation_name>` in bold.
2. **Line 2:** `explanation` — one sentence, always under 120 characters.
3. **Separator**
4. **Remedy:** Full remediation guidance paragraph (from `Finding.remedy`).
5. **Source:** `AI Ethics · <jurisdiction>`

### 10.7 Status Bar Item

A persistent status bar item at the right edge shows the current state:

| State       | Label                                   |
| ----------- | --------------------------------------- |
| Idle        | `$(shield) AI Ethics`                   |
| Scheduled   | `$(clock) AI Ethics: Check in 5s…`      |
| Running     | `$(sync~spin) AI Ethics: Analysing…`    |
| Clean       | `$(check) AI Ethics: Clean`             |
| Violations  | `$(error) AI Ethics: 3 violations`      |
| Error       | `$(warning) AI Ethics: Error`           |

Clicking the status bar item opens the Problems panel filtered to `AI Ethics` source.

### 10.8 VS Code Settings

```jsonc
// package.json contributes.configuration
{
  "aiEthics.enabled":    { "type": "boolean", "default": true },
  "aiEthics.provider":   { "type": "string",  "default": "ollama_cloud",
                           "enum": ["ollama_cloud", "openrouter", "groq", "ollama_local"] },
  "aiEthics.model":      { "type": "string",  "default": "glm4:cloud" },
  "aiEthics.pythonPath": { "type": "string",  "default": "python",
                           "description": "Path to Python interpreter running the MCP server" },
  "aiEthics.serverPath": { "type": "string",  "default": "",
                           "description": "Absolute path to mcp_server.py" },
  "aiEthics.debounceMs": { "type": "number",  "default": 5000,
                           "description": "Milliseconds to wait after last change before running check" }
}
```

---

## 11. Report Specification

Each `write_report` node execution produces a per-file Markdown report at `compliance-analysis/{filename}_analysis_report.md`. The report is structured as follows:

```markdown
# Compliance Report: {file_path}
**Status:** FAIL  |  **Findings:** 3
**Summary:** {one-paragraph summary of the file's purpose and compliance posture}

## Findings

### 1. [HIGH] EU AI Act — Article 13 Transparency
**Lines:** 42–57  |  **Jurisdiction:** EU
**Issue:** {explanation}
**Remedy:** {remedy}

### 2. [MEDIUM] IEEE Ethically Aligned Design — Principle 4
...
```

HTML output is not generated in v4.0 (Streamlit removed). If a rendered report is needed, the extension's output webview renders the Markdown inline.

---

## 12. Project Directory Structure

```
ai-ethics-compliance-agent/
│
├── mcp_server.py                   # MCP server entry point — stdio transport
├── config.yaml
├── .env.example
├── requirements.txt
├── README.md
│
├── ai_ethics_knowledge_base.pdf    # User-supplied — MUST exist at project root
│
├── graphs/
│   ├── __init__.py
│   ├── compliance_graph.py         # Main StateGraph: initialize → review_file → write_report
│   ├── file_review_subgraph.py     # create_react_agent for file review
│   └── checkpointer.py             # SqliteSaver / PostgresSaver factory
│
├── nodes/
│   ├── __init__.py
│   ├── initialize.py
│   ├── review_file.py
│   └── write_report.py
│
├── tools/
│   ├── __init__.py
│   ├── filesystem_tools.py         # read_file, write_file, safe_mkdir
│   └── rag_tool.py                 # query_rag LangChain Tool
│
├── rag/
│   ├── __init__.py
│   ├── ingestor.py
│   └── retriever.py
│
├── llm/
│   ├── __init__.py
│   └── provider_factory.py
│
├── models/
│   ├── __init__.py
│   ├── state.py                    # ComplianceState, FileResult, Finding, ProgressEvent
│   └── events.py
│
├── tracing/
│   ├── __init__.py
│   └── langsmith_setup.py
│
├── prompts/
│   ├── loader.py
│   └── file_reviewer.md
│
├── vscode-extension/               # TypeScript VS Code extension package
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── extension.ts            # Activation, debounce, MCP client
│       ├── diagnostics.ts          # findingToDiagnostic, DiagnosticCollection management
│       ├── mcpClient.ts            # MCP stdio client wrapper + streaming
│       └── statusBar.ts            # Status bar item management
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
  rate_limit_rps: 2
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
      models: []

rag:
  knowledge_base_pdf: ai_ethics_knowledge_base.pdf
  chroma_persist_dir: .chroma_db
  collection_name: ai_ethics_kb
  chunk_size: 800
  chunk_overlap: 100
  top_k: 5
  embedding_model: all-MiniLM-L6-v2

scan:
  output_dir: compliance-analysis
  max_file_size_mb: 50

filesystem:
  write_lock_timeout_s: 30
  read_retry_attempts: 3
  read_retry_min_wait_s: 0.5
  read_retry_max_wait_s: 4.0

checkpoint:
  backend: sqlite
  sqlite_path: .langgraph_checkpoints.db
  postgres_uri_env: POSTGRES_URI

langsmith:
  project: ai-ethics-compliance-agent
  endpoint: https://api.smith.langchain.com
  tracing_v2: true

extension:
  debounce_ms: 5000   # milliseconds after last change before agent fires
```

**`.env.example`:**

```
# LLM Providers
OLLAMA_CLOUD_API_KEY=your_ollama_cloud_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
GROQ_API_KEY=your_groq_key_here

# LangSmith Tracing
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true

# Checkpoint Backend
CHECKPOINT_BACKEND=sqlite
CHECKPOINT_DB_PATH=.langgraph_checkpoints.db
```

---

## 14. Python Dependencies

**`requirements.txt`:**

```
# LangGraph + LangChain Core
langgraph>=0.2.0
langgraph-checkpoint-sqlite>=0.1.0
langgraph-checkpoint-postgres>=0.1.0
langchain>=0.2.0
langchain-community>=0.2.0
langchain-core>=0.2.0

# LLM Providers
langchain-ollama>=0.1.0
langchain-openai>=0.1.0
langchain-groq>=0.1.0

# LangSmith
langsmith>=0.1.0

# RAG
chromadb>=0.5.0
sentence-transformers>=3.0.0
PyMuPDF>=1.24.0

# Filesystem Robustness
filelock>=3.14.0
chardet>=5.2.0

# Data Parsing
python-docx>=1.1.0

# Retry Logic
tenacity>=8.2.0

# MCP Server
mcp>=1.0.0

# Config
python-dotenv>=1.0.0
pyyaml>=6.0.0
```

---

## 15. End-to-End Data Flow

```
User writes code in VS Code
 │
 ├─1─► vscode.workspace.onDidChangeTextDocument fires on every keystroke
 │       └─ scheduleCheck(document) — resets 5s debounce timer
 │
 ├─2─► 5 seconds after last change, debounce fires
 │       └─ isWritingOnLastLine() check — if still typing on last line, push back
 │          else: runComplianceCheck(document)
 │
 ├─3─► Extension calls MCP tool: check_file(file_path, file_content, provider, model)
 │       └─ MCP server receives over stdio
 │          thread_id = uuid4()
 │          config = get_run_config(thread_id, ...)
 │          asyncio.run( stream_compliance_check(graph, ...) )
 │
 ├─4─► LangGraph: START → initialize node
 │       └─ @traceable: "initialize"
 │          validate inputs, safe_mkdir(output_dir)
 │          emit ProgressEvent: scan_started
 │          LangSmith: span logged
 │
 ├─5─► LangGraph: initialize → review_file node
 │       └─ @traceable: "review_file:{basename}"
 │          create_react_agent invoked with file content
 │          ├─ LLM: classify file type, predict output
 │          ├─ Tool: query_rag(@traceable) → top-5 regulation chunks
 │          ├─ LLM: reason about violations → list[Finding]
 │          ├─ For each Finding: write_stream(violation_found event) ← streamed immediately
 │          └─ Tool: write_file(@traceable) → per-file analysis report
 │
 ├─6─► astream_events proxy: on_custom_event(violation_found)
 │       └─ MCP server proxies event to extension
 │          Extension: findingToDiagnostic() → DiagnosticCollection.set()
 │          VS Code renders red/yellow squiggle in real-time
 │
 ├─7─► LangGraph: review_file → write_report node
 │       └─ @traceable: "write_report"
 │          serialise FileResult → Markdown report
 │          write_file_tool(atomic) → {basename}_analysis_report.md
 │          state.scan_complete = True
 │          LangSmith: top-level span closed
 │
 ├─8─► astream_events: on_chain_end(write_report)
 │       └─ MCP server emits scan_complete event
 │          Extension: status bar → "$(check) AI Ethics: N violations"
 │          LangSmith run URL logged to extension output panel
 │
 └─9─► User hovers squiggle in editor
         └─ VS Code hover card shows: severity, regulation name, explanation, remedy
            Problems panel shows full finding list filtered to "AI Ethics"
```

---

## 16. MCP Server

The MCP server is the bridge between the VS Code extension (TypeScript) and the LangGraph compliance graph (Python). It runs as a subprocess started by the extension and communicates via stdin/stdout.

```python
# mcp_server.py
import asyncio, uuid, json
from mcp import MCPServer, tool
from graphs.compliance_graph import compile_graph
from tracing.langsmith_setup import get_run_config
from rag.ingestor import ingest, needs_ingestion
from config_loader import load_config

server = MCPServer(name="ai-ethics-compliance-agent")
graph  = compile_graph()

# Auto-ingest on startup
if needs_ingestion():
    print("Ingesting knowledge base…", flush=True)
    ingest()

@server.tool()
async def check_file(
    file_path: str,
    file_content: str,
    provider: str = "ollama_cloud",
    model: str = "glm4:cloud",
) -> dict:
    """
    Run an AI ethics compliance check on the given file content.
    Streams violation_found events as findings are discovered.
    Returns the complete FileResult when done.
    """
    thread_id = str(uuid.uuid4())
    config    = get_run_config(thread_id, file_path, provider, model)

    initial_state = {
        "file_path":    file_path,
        "file_content": file_content,
        "llm_provider": provider,
        "llm_model":    model,
        "config":       load_config(),
    }

    findings = []
    async for event in graph.astream_events(initial_state, config=config, version="v2"):
        kind = event["event"]
        data = event.get("data", {})

        # Proxy custom events (violation_found, progress) to the MCP response stream
        if kind == "on_custom_event":
            yield {"type": event["name"], "data": data}

        elif kind == "on_chain_end" and event.get("name") == "write_report":
            output = data.get("output", {})
            yield {
                "type": "scan_complete",
                "data": {
                    "file_result":       output.get("file_result"),
                    "final_report_md":   output.get("final_report_md"),
                    "langsmith_run_url": output.get("langsmith_run_url"),
                },
            }

if __name__ == "__main__":
    server.run(transport="stdio")
```

---

## 17. Acceptance Criteria

| ID    | Criterion                                                                                                    | Verification                                                     |
| ----- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| AC-01 | MCP server starts without errors when `ai_ethics_knowledge_base.pdf` is present                              | `python mcp_server.py` → no crash                                |
| AC-02 | RAG auto-ingested on first MCP server start; chunk count > 0 in logs                                         | Log output shows `✓ Ingested N chunks`                           |
| AC-03 | VS Code extension activates and registers `onDidChangeTextDocument` listener without error                   | Extension log: no activation errors                              |
| AC-04 | Agent does NOT fire on every keystroke — fires exactly 5 seconds after the last change                       | Timed observation; check server logs                             |
| AC-05 | Agent does NOT fire while cursor is on the last line and that line has content                                | Type on last line; observe no check fires while typing           |
| AC-06 | A known HIGH violation in a seeded test file produces a red squiggle on the correct lines                    | Manual review; Problems panel shows correct line range           |
| AC-07 | Hover card shows: severity, regulation name, explanation, remedy                                             | Visual inspection                                                |
| AC-08 | Diagnostics update incrementally as findings stream — not all at once at the end                             | Watch Problems panel during a check on a file with 3+ violations |
| AC-09 | Status bar updates through all states: idle → scheduled → analysing → done                                   | Visual observation                                               |
| AC-10 | Switching LLM provider in VS Code settings takes effect on the next check without restarting the extension   | Change provider; trigger check; server log shows new provider    |
| AC-11 | All 4 LLM providers produce a non-empty FileResult for a test file                                           | Manual test each provider                                        |
| AC-12 | LLM retry logic fires on transient failure; node not marked ERROR until 3 attempts exhausted                 | Simulated failure; LangSmith trace shows retries                 |
| AC-13 | `ComplianceState` is JSON-serialisable (`json.dumps(state)` passes)                                          | Automated test                                                   |
| AC-14 | LangSmith trace is created for every check and visible in LangSmith UI                                       | Open LangSmith after check                                       |
| AC-15 | Every node appears as a named child span in the LangSmith trace                                              | Visual inspection in LangSmith                                   |
| AC-16 | Path traversal attack in file path input is rejected by `_safe_path()`                                       | Unit test: `read_file("../../etc/passwd")` raises ValueError     |
| AC-17 | Binary files are gracefully skipped — extension shows `$(shield) AI Ethics: Skipped`                        | Open a `.png`; verify no crash                                   |
| AC-18 | MCP server handles concurrent check requests without corrupting state (each has its own `thread_id`)         | Rapid file switching stress test                                 |
| AC-19 | Atomic file writes succeed for the per-file report (no partial files)                                        | Write stress test                                                |
| AC-20 | Extension output panel shows LangSmith run URL after each completed check                                    | Visual inspection                                                |

---

## 18. Open Questions

| #    | Question                                                                                    | Recommendation                                                                                               |
| ---- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| OQ-1 | What is the max context window of `glm4:cloud`?                                             | Check Ollama Cloud docs. If < 8K tokens, implement line-range chunking in `read_file` calls within Reviewer. |
| OQ-2 | Should `compliance-analysis/` be created inside the workspace root or the project root?    | Workspace root — keeps outputs co-located with the code being checked.                                       |
| OQ-3 | Should the MCP server be a long-running process or re-spawned per check?                   | Long-running — avoids ChromaDB and model loading overhead on every check. Extension manages lifecycle.        |
| OQ-4 | Should the extension support multi-root workspaces (one MCP server per root)?              | Single server per workspace in v4.0; multi-root in a future milestone.                                       |
| OQ-5 | Should `SqliteSaver` be WAL-mode for better concurrent write performance?                  | Yes — set `PRAGMA journal_mode=WAL` on the SQLite connection at startup.                                     |
| OQ-6 | Should LangSmith tracing be optional (graceful degradation if `LANGSMITH_API_KEY` absent)? | Yes — if key is absent, skip tracer callback. All `@traceable` decorators are no-ops without the key.       |
| OQ-7 | What file types should trigger a compliance check? All, or code-only?                      | All text-based files by default; configurable per-extension list in `config.yaml`.                           |

---
