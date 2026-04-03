# AI Ethics Compliance Agent

## Product Requirements Document — v4.0

_April 2026 · Status: DRAFT · Priority: P0_

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [System Architecture](#3-system-architecture)
4. [LangGraph Graph — Simplified & Streaming](#4-langgraph-graph--simplified--streaming)
5. [Agent & Node Catalogue](#5-agent--node-catalogue)
6. [Tool Catalogue](#6-tool-catalogue)
7. [LLM Provider System](#7-llm-provider-system)
8. [RAG Knowledge Base](#8-rag-knowledge-base)
9. [LangSmith Tracing](#9-langsmith-tracing)
10. [VS Code Extension — Primary Deliverable](#10-vs-code-extension--primary-deliverable)
11. [Report Specification](#11-report-specification)
12. [Project Directory Structure](#12-project-directory-structure)
13. [Configuration Reference](#13-configuration-reference)
14. [Python Dependencies](#14-python-dependencies)
15. [End-to-End Data Flow](#15-end-to-end-data-flow)
16. [Acceptance Criteria](#16-acceptance-criteria)
17. [Open Questions](#17-open-questions)
18. [Revision History](#18-revision-history)

---

## 1. Executive Summary

The **AI Ethics Compliance Agent** is an autonomous, multi-agent orchestration system built on **LangGraph** that analyses source code for AI ethics violations in **real-time** — surfaced directly in **VS Code** as inline diagnostics, just like a type-checker.

**v4.0 breaking changes vs v3.0:**

- **Streamlit UI removed entirely.** The Python backend is now a headless library + optional CLI. All user interaction happens inside VS Code.
- **LangGraph graph simplified.** The `validate_data_source` node and its conditional edge are removed. The graph is now a clean linear fan-out: `initialize → fan_out → review_file* → join → write_reports → END`.
- **LangGraph streaming enabled.** The backend exposes `graph.astream_events()` over a local HTTP server (FastAPI/SSE). The VS Code extension consumes this stream to update diagnostics token-by-token.
- **VS Code Extension is now the primary UI.** It watches active documents, debounces changes (5 s), fires the agent, and renders pass/fail decorations + diagnostics inline — identical to how TypeScript or Pylance errors appear.

---

## 2. Goals & Non-Goals

### 2.1 Goals

- **Real-time in-editor compliance**: Analyse edited files within 5 s of the last keystroke and render inline diagnostics without leaving VS Code.
- **Streaming agent output**: Surface agent reasoning and partial results incrementally via `astream_events`, giving the user live feedback rather than a delayed bulk result.
- **Simplified graph**: Linear `START → initialize → fan_out → review_file* → join → write_reports → END` — no conditional edges, no nested data-source validator subgraph.
- **Headless Python backend**: Runs as a local FastAPI server (`python -m ethics_agent.server`). The VS Code extension talks to it over HTTP/SSE.
- **Inline VS Code diagnostics**: `HIGH` findings → Error (red), `MEDIUM` → Warning (amber), `LOW` → Hint (blue). Diagnostic message = short description. Hover panel = remedy text.
- **Per-file and consolidated reports**: Written to `compliance-analysis/` as Markdown (HTML optional).
- **Full LangSmith observability**: Every node, LLM call, tool call traced.
- **Scan resumption**: `SqliteSaver` checkpointing — re-running the same `thread_id` skips completed nodes.

### 2.2 Non-Goals (v4.0)

- Streamlit or any browser-based UI.
- `validate_data_source` subgraph (deferred to v5.0).
- Automatic remediation (flagging only).
- MCP server (deferred).
- Support for compiled binaries without source.

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌─────────────────────────────────────────────────┐
│              VS CODE EXTENSION (TypeScript)      │
│  onDidChangeTextDocument → 5 s debounce         │
│  → POST /scan  { file_path, content }           │
│  ← SSE stream  (astream_events)                 │
│  → vscode.languages.createDiagnosticCollection  │
│  → vscode.window.createTextEditorDecorationType │
└──────────────────────┬──────────────────────────┘
                       │ HTTP / SSE (localhost)
                       ▼
┌─────────────────────────────────────────────────┐
│       FASTAPI LOCAL SERVER  (Python)            │
│  POST /scan  → enqueue scan task                │
│  GET  /scan/{id}/stream  → SSE astream_events   │
│  GET  /health                                   │
└──────────────────────┬──────────────────────────┘
                       │ invokes
                       ▼
┌─────────────────────────────────────────────────┐
│          LANGGRAPH COMPLIANCE GRAPH             │
│  START → initialize → fan_out                  │
│        → review_file × N (parallel, Send API)  │
│        → join_results → write_reports → END    │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │       SHARED TOOLS      │
          │  read_file  write_file  │
          │  query_rag  run_bash    │
          └─────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │       LANGSMITH         │
          │  Full trace per run     │
          │  Nested spans per node  │
          └─────────────────────────┘
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
    explanation: str        # short — shown in VS Code hover
    remedy: str             # shown on expand / hover detail
    rag_chunk_id: str

class FileResult(TypedDict):
    file_path: str
    file_type: str
    language: str | None
    status: str             # PASS | WARN | FAIL | ERROR | SKIPPED
    summary: str
    findings: list[Finding]
    report_path: str | None
    error: str | None

class ProgressEvent(TypedDict):
    event_type: str         # scan_started | file_started | file_complete | violation_found | scan_complete | error
    file_path: str
    message: str
    timestamp: str

class ComplianceState(TypedDict):
    # Input
    target_directory: str
    config: dict[str, Any]
    llm_provider: str
    llm_model: str

    # Discovery
    all_files: list[str]
    skipped_files: list[str]

    # Per-file results — safe concurrent appends via operator.add
    file_results: Annotated[list[FileResult], operator.add]

    # Progress events — streamed to VS Code extension
    progress_events: Annotated[list[ProgressEvent], operator.add]

    # Final outputs
    final_report_md: str | None
    scan_complete: bool
    scan_error: str | None

    # LangSmith
    langsmith_run_id: str | None
    langsmith_run_url: str | None
```

**Key additions vs v3.0:**
- `Finding.remedy` — required field; rendered in VS Code hover detail panel.
- `validate_data_source` related fields (`_pending_data_sources`, `_current_file_result`, `final_report_html`) removed.

---

## 4. LangGraph Graph — Simplified & Streaming

### 4.1 Graph Definition (`graphs/compliance_graph.py`)

The graph is now **strictly linear with a single fan-out**. There are no conditional edges inside the file-processing path.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langchain_core.runnables import RunnableConfig

from models.state import ComplianceState
from nodes.initialize import initialize_node
from nodes.fan_out import fan_out_files_node
from nodes.review_file import review_file_node
from nodes.join_results import join_results_node
from nodes.write_reports import write_reports_node
from graphs.checkpointer import get_checkpointer

def build_compliance_graph() -> StateGraph:
    builder = StateGraph(ComplianceState)

    builder.add_node("initialize",    initialize_node)
    builder.add_node("fan_out",       fan_out_files_node)
    builder.add_node("review_file",   review_file_node)
    builder.add_node("join_results",  join_results_node)
    builder.add_node("write_reports", write_reports_node)

    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "fan_out")

    # Fan-out: one Send per file → all run in parallel
    builder.add_conditional_edges(
        "fan_out",
        lambda state: [
            Send("review_file", {**state, "_current_file": fp})
            for fp in state["all_files"]
        ] or [Send("join_results", state)],  # empty-dir guard
    )

    # All parallel branches converge at join_results (LangGraph barrier)
    builder.add_edge("review_file",   "join_results")
    builder.add_edge("join_results",  "write_reports")
    builder.add_edge("write_reports", END)

    return builder

def compile_graph(checkpointer=None):
    builder = build_compliance_graph()
    cp = checkpointer or get_checkpointer()
    return builder.compile(checkpointer=cp)
```

### 4.2 Streaming via `astream_events` (FastAPI SSE endpoint)

The FastAPI server exposes the graph's `astream_events` as a Server-Sent Events stream. The VS Code extension subscribes to this stream:

```python
# server/main.py
import asyncio, uuid, json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graphs.compliance_graph import compile_graph
from tracing.langsmith_setup import get_run_config

app = FastAPI()
_graph = compile_graph()

class ScanRequest(BaseModel):
    target_directory: str
    llm_provider: str = "ollama_cloud"
    llm_model: str    = "glm4:cloud"
    file_paths: list[str] | None = None   # None = scan whole dir

@app.post("/scan")
async def start_scan(req: ScanRequest):
    thread_id = str(uuid.uuid4())
    return {"scan_id": thread_id}

@app.get("/scan/{scan_id}/stream")
async def stream_scan(scan_id: str, target_directory: str,
                      llm_provider: str = "ollama_cloud",
                      llm_model: str = "glm4:cloud"):
    """SSE endpoint — streams LangGraph astream_events to the VS Code extension."""

    initial_state = {
        "target_directory": target_directory,
        "llm_provider":     llm_provider,
        "llm_model":        llm_model,
        "config":           _load_config(),
        "file_results":     [],
        "progress_events":  [],
        "all_files":        [],
        "skipped_files":    [],
        "scan_complete":    False,
        "scan_error":       None,
        "final_report_md":  None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }
    config = get_run_config(scan_id, target_directory, llm_provider, llm_model)

    async def event_generator():
        async for event in _graph.astream_events(
            initial_state, config=config, version="v2"
        ):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)
        yield "data: {\"event\": \"stream_end\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 4.3 Event Types Consumed by VS Code Extension

| `event` field        | `name` filter          | VS Code action                                    |
|----------------------|------------------------|---------------------------------------------------|
| `on_chain_start`     | `review_file`          | Set file decoration → 🔄 SCANNING                |
| `on_chat_model_stream` | any                  | Append token to status bar streaming indicator    |
| `on_chain_end`       | `review_file`          | Parse `FileResult`, push diagnostics to collection|
| `on_tool_start`      | `query_rag`            | Status bar: "Querying ethics knowledge base…"     |
| `on_chain_end`       | `write_reports`        | Notify: "Compliance report written"               |
| `stream_end`         | —                      | Clear scanning decoration, finalize diagnostics   |

### 4.4 Checkpointer (`graphs/checkpointer.py`)

```python
import os
from langgraph.checkpoint.sqlite import SqliteSaver

CHECKPOINT_DB = os.getenv("CHECKPOINT_DB_PATH", ".langgraph_checkpoints.db")

def get_checkpointer():
    backend = os.getenv("CHECKPOINT_BACKEND", "sqlite")
    if backend == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver
        uri = os.getenv("POSTGRES_URI")
        if not uri:
            raise EnvironmentError("POSTGRES_URI must be set")
        return PostgresSaver.from_conn_string(uri)
    return SqliteSaver.from_conn_string(CHECKPOINT_DB)
```

---

## 5. Agent & Node Catalogue

| Node            | Type        | Prompt File                | Parallel?      | Tools                              |
|-----------------|-------------|----------------------------|----------------|------------------------------------|
| `initialize`    | Pure Python | —                          | No             | —                                  |
| `fan_out`       | Pure Python | —                          | No             | `list_directory_robust` (direct)   |
| `review_file`   | ReAct Agent | `prompts/file_reviewer.md` | Yes (via Send) | `read_file`, `write_file`, `query_rag`, `run_bash` |
| `join_results`  | Pure Python | —                          | No (barrier)   | —                                  |
| `write_reports` | ReAct Agent | `prompts/report_writer.md` | No             | `write_file`, `read_file`          |

### 5.1 `initialize` Node

```python
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import safe_mkdir
from datetime import datetime, timezone
import os

@traceable(name="initialize", tags=["compliance-scan", "setup"])
def initialize_node(state: ComplianceState) -> dict:
    target = state["target_directory"]
    if not os.path.isdir(target):
        return {"scan_error": f"Directory not found: {target}"}
    output_dir = os.path.join(target, state["config"]["scan"]["output_dir"])
    safe_mkdir(output_dir)
    event = ProgressEvent(
        event_type="scan_started", file_path="",
        message=f"Scan started. Target: {target}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"progress_events": [event]}
```

### 5.2 `fan_out` Node

```python
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import list_directory_robust
from datetime import datetime, timezone
import os

@traceable(name="fan_out", tags=["compliance-scan", "discovery"])
def fan_out_files_node(state: ComplianceState) -> dict:
    config   = state["config"]
    skip_ext = set(config["scan"]["skip_extensions"])
    max_mb   = config["scan"]["max_file_size_mb"]

    all_paths = list_directory_robust(state["target_directory"], recursive=True)
    accepted, skipped = [], []
    for entry in all_paths:
        fp  = entry["path"]
        ext = os.path.splitext(fp)[1].lower()
        mb  = entry["size_bytes"] / (1024 * 1024)
        if ext in skip_ext or mb > max_mb:
            skipped.append(fp)
        else:
            accepted.append(fp)

    event = ProgressEvent(
        event_type="discovery_complete", file_path="",
        message=f"Discovered {len(accepted)} files ({len(skipped)} skipped).",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"all_files": accepted, "skipped_files": skipped, "progress_events": [event]}
```

### 5.3 `review_file` Node

```python
from langsmith import traceable
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from models.state import ComplianceState, FileResult, ProgressEvent
from tools.filesystem_tools import read_file_tool, write_file_tool, run_bash_tool
from tools.rag_tool import query_rag_tool
from llm.provider_factory import create_llm
from prompts.loader import load_prompt
from datetime import datetime, timezone
import os, json, re

@traceable(name="review_file", tags=["compliance-scan", "file-review"])
def review_file_node(state: ComplianceState) -> dict:
    file_path = state["_current_file"]
    llm       = create_llm(state["llm_provider"], state["llm_model"])
    agent     = create_react_agent(
        model=llm,
        tools=[read_file_tool, write_file_tool, run_bash_tool, query_rag_tool],
        state_modifier=SystemMessage(content=load_prompt("file_reviewer")),
    )

    start_event = ProgressEvent(
        event_type="file_started", file_path=file_path,
        message=f"Reviewing: {os.path.basename(file_path)}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    output_dir = os.path.join(state["target_directory"], state["config"]["scan"]["output_dir"])
    prompt = (
        f"Analyse for AI ethics compliance. File: {file_path}\n"
        f"Report output dir: {output_dir}\n"
        f"Return FileResult JSON in <RESULT>...</RESULT> tags. "
        f"Every Finding MUST include remedy field (remediation advice)."
    )

    try:
        result     = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=RunnableConfig(tags=["file-review", os.path.basename(file_path)],
                                  metadata={"file_path": file_path}),
        )
        final_msg  = result["messages"][-1].content
        match      = re.search(r"<RESULT>(.*?)</RESULT>", final_msg, re.DOTALL)
        file_result: FileResult = json.loads(match.group(1)) if match else _error_result(file_path, "No RESULT tag")
    except Exception as e:
        file_result = _error_result(file_path, str(e))

    done_event = ProgressEvent(
        event_type="file_complete", file_path=file_path,
        message=f"{os.path.basename(file_path)} → {file_result['status']} ({len(file_result['findings'])} findings)",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"file_results": [file_result], "progress_events": [start_event, done_event]}

def _error_result(file_path: str, error: str) -> FileResult:
    return FileResult(
        file_path=file_path, file_type="unknown", language=None,
        status="ERROR", summary="", findings=[], report_path=None, error=error,
    )
```

### 5.4 `join_results` Node

```python
from langsmith import traceable
from models.state import ComplianceState, ProgressEvent
from datetime import datetime, timezone

@traceable(name="join_results", tags=["compliance-scan", "aggregation"])
def join_results_node(state: ComplianceState) -> dict:
    # De-duplicate: keep last (most complete) result per file_path
    seen = {}
    for r in state["file_results"]:
        seen[r["file_path"]] = r
    deduped = list(seen.values())
    event = ProgressEvent(
        event_type="aggregation_complete", file_path="",
        message=f"Aggregated {len(deduped)} file results.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"file_results": deduped, "progress_events": [event]}
```

### 5.5 `write_reports` Node

```python
from langsmith import traceable
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from models.state import ComplianceState, ProgressEvent
from tools.filesystem_tools import write_file_tool, read_file_tool
from llm.provider_factory import create_llm
from prompts.loader import load_prompt
from datetime import datetime, timezone
import os, json, re

@traceable(name="write_reports", tags=["compliance-scan", "reporting"])
def write_reports_node(state: ComplianceState) -> dict:
    llm   = create_llm(state["llm_provider"], state["llm_model"])
    agent = create_react_agent(
        model=llm,
        tools=[write_file_tool, read_file_tool],
        state_modifier=SystemMessage(content=load_prompt("report_writer")),
    )
    output_dir   = os.path.join(state["target_directory"], state["config"]["scan"]["output_dir"])
    results_json = json.dumps(state["file_results"], indent=2)

    prompt = (
        f"Write a consolidated compliance report.\n"
        f"Output dir: {output_dir}\n"
        f"File results:\n{results_json}\n"
        f"Write final_compliance_report.md. Return path in <RESULT>{{\"md_path\": \"...\"}}</RESULT>."
    )
    result  = agent.invoke({"messages": [{"role": "user", "content": prompt}]},
                           config=RunnableConfig(tags=["report-writing"]))
    final   = result["messages"][-1].content
    match   = re.search(r"<RESULT>(.*?)</RESULT>", final, re.DOTALL)
    md_path = json.loads(match.group(1)).get("md_path", "") if match else ""
    md_content = ""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
    except Exception:
        pass

    event = ProgressEvent(
        event_type="scan_complete", file_path="",
        message="Final compliance report written.",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return {"final_report_md": md_content, "scan_complete": True, "progress_events": [event]}
```

---

## 6. Tool Catalogue

| Tool                    | Module                      | Available To                    | Description                                               |
|-------------------------|-----------------------------|---------------------------------|-----------------------------------------------------------|
| `list_directory_robust` | `tools/filesystem_tools.py` | `fan_out` (direct)              | Recursive file listing with retry, symlink-safe           |
| `read_file_tool`        | `tools/filesystem_tools.py` | `review_file`, `write_reports`  | Read with retry, encoding detection, path traversal guard |
| `write_file_tool`       | `tools/filesystem_tools.py` | `review_file`, `write_reports`  | Atomic write via temp+rename, file locking                |
| `run_bash_tool`         | `tools/filesystem_tools.py` | `review_file`                   | Shell command with timeout, non-zero exit → ToolException |
| `query_rag_tool`        | `tools/rag_tool.py`         | `review_file`                   | Semantic search against ChromaDB ethics knowledge base    |

> **Note:** `web_search_tool` and `validate_data_source` subgraph removed in v4.0. Deferred to v5.0.

---

## 7. LLM Provider System

### 7.1 Supported Providers

| Provider Key   | Display Name   | Suggested Models                                                     | Auth                   |
|----------------|----------------|----------------------------------------------------------------------|------------------------|
| `ollama_cloud` | Ollama Cloud _(default)_ | `glm4:cloud`, `llama3.3:cloud`, `qwen2.5:cloud`         | `OLLAMA_CLOUD_API_KEY` |
| `openrouter`   | OpenRouter     | `anthropic/claude-3.5-sonnet`, `openai/gpt-4o`                       | `OPENROUTER_API_KEY`   |
| `groq`         | Groq           | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`                      | `GROQ_API_KEY`         |
| `ollama_local` | Ollama Local   | Auto-detected via `ollama list`                                      | None                   |

### 7.2 Provider Factory (`llm/provider_factory.py`)

```python
import os
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

def create_llm(provider: str, model: str, **kwargs) -> BaseChatModel:
    rate_limiter = InMemoryRateLimiter(requests_per_second=2, max_bucket_size=10)

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model, base_url="https://cloud.ollama.com",
                         api_key=os.getenv("OLLAMA_CLOUD_API_KEY"),
                         rate_limiter=rate_limiter, **kwargs)
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model, base_url="https://openrouter.ai/api/v1",
                         api_key=os.getenv("OPENROUTER_API_KEY"),
                         rate_limiter=rate_limiter, **kwargs)
    elif provider == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(model=model, api_key=os.getenv("GROQ_API_KEY"),
                       rate_limiter=rate_limiter, **kwargs)
    elif provider == "ollama_local":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model, base_url="http://localhost:11434",
                         rate_limiter=rate_limiter, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
```

---

## 8. RAG Knowledge Base

### 8.1 Source

- **File:** `knowledge/ai_ethics_knowledge_base.pdf`
- **Auto-ingested** on first server start if `.chroma_db/` is empty.
- **Manual rebuild:** `python scripts/ingest_knowledge_base.py`

### 8.2 Ingestion (`rag/ingestor.py`)

```python
import fitz, chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langsmith import traceable

CHROMA_PATH = ".chroma_db"
COLLECTION  = "ai_ethics_kb"
PDF_PATH    = "knowledge/ai_ethics_knowledge_base.pdf"

@traceable(name="rag_ingest", tags=["rag", "setup"])
def ingest():
    doc    = fitz.open(PDF_PATH)
    pages  = [{"text": page.get_text(), "page": i+1} for i, page in enumerate(doc)]
    sp     = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks, metas, ids = [], [], []
    for p in pages:
        for j, chunk in enumerate(sp.split_text(p["text"])):
            cid = f"p{p['page']}_c{j}"
            chunks.append(chunk)
            metas.append({"page": p["page"], "source": PDF_PATH, "chunk_id": cid})
            ids.append(cid)
    embedder   = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectors    = embedder.embed_documents(chunks)
    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION)
    collection.add(documents=chunks, embeddings=vectors, metadatas=metas, ids=ids)
    print(f"✓ Ingested {collection.count()} chunks")
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
        return [
            {"text": doc, "metadata": results["metadatas"][0][i], "score": results["distances"][0][i]}
            for i, doc in enumerate(results["documents"][0])
        ]
```

---

## 9. LangSmith Tracing

### 9.1 Environment

```bash
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_TRACING_V2=true
```

All LangGraph / LangChain calls are auto-traced. Explicit `@traceable` on pure-Python nodes ensures 100% coverage.

### 9.2 Run Config (`tracing/langsmith_setup.py`)

```python
import os
from langchain.callbacks.tracers import LangChainTracer

LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")

def get_run_config(thread_id: str, target_dir: str, provider: str, model: str) -> dict:
    tracer = LangChainTracer(project_name=LANGSMITH_PROJECT)
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks":    [tracer],
        "tags":         ["compliance-scan", f"provider:{provider}", f"model:{model}"],
        "metadata":     {"thread_id": thread_id, "target_directory": target_dir,
                         "llm_provider": provider, "llm_model": model},
        "run_name":     f"ComplianceScan-{thread_id[:8]}",
    }
```

---

## 10. VS Code Extension — Primary Deliverable

### 10.1 Extension Overview

The VS Code extension (`vscode-ethics-agent/`) is the **primary user interface**. It:

1. Watches the active text editor for changes.
2. Debounces 5 seconds after the last change before firing a scan.
3. Detects whether the cursor is on the last line (confirming active coding).
4. Sends the current file to the local FastAPI backend.
5. Consumes the SSE stream and renders inline diagnostics in real-time.
6. Shows `FAILED` decorations in red beside failing line ranges, with short descriptions.
7. Expands to show remedy text in the hover panel (like TypeScript errors).

### 10.2 Extension Entry Point (`vscode-ethics-agent/src/extension.ts`)

```typescript
import * as vscode from 'vscode';
import { EthicsAgentClient } from './client';
import { DiagnosticsManager } from './diagnostics';

let debounceTimer: NodeJS.Timeout | undefined;
const DEBOUNCE_MS = 5000;

export function activate(context: vscode.ExtensionContext) {
    const client      = new EthicsAgentClient();
    const diagnostics = new DiagnosticsManager();

    // Listen for every document change
    const changeListener = vscode.workspace.onDidChangeTextDocument(async (event) => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || event.document !== editor.document) return;

        // Check if user is writing at/near the last line
        const doc        = event.document;
        const cursorLine = editor.selection.active.line;
        const lastLine   = doc.lineCount - 1;
        const isAtEnd    = cursorLine >= lastLine - 2;  // within 2 lines of bottom

        // Reset debounce timer
        if (debounceTimer) clearTimeout(debounceTimer);

        debounceTimer = setTimeout(async () => {
            const filePath = doc.uri.fsPath;
            if (!isSupported(doc.languageId)) return;

            diagnostics.setScanning(filePath);
            await client.scanFile(filePath, doc.getText(), diagnostics);
        }, DEBOUNCE_MS);
    });

    context.subscriptions.push(changeListener, diagnostics);
}

function isSupported(languageId: string): boolean {
    const supported = ['python', 'typescript', 'javascript', 'java', 'go', 'rust', 'cpp', 'c'];
    return supported.includes(languageId);
}

export function deactivate() {
    if (debounceTimer) clearTimeout(debounceTimer);
}
```

### 10.3 Backend Client (`vscode-ethics-agent/src/client.ts`)

```typescript
import * as vscode from 'vscode';
import * as http from 'http';
import { DiagnosticsManager } from './diagnostics';

const SERVER_BASE = 'http://localhost:8765';

export class EthicsAgentClient {
    async scanFile(filePath: string, content: string, dm: DiagnosticsManager): Promise<void> {
        const config = vscode.workspace.getConfiguration('ethicsAgent');
        const dir    = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';
        const provider = config.get<string>('provider', 'ollama_cloud');
        const model    = config.get<string>('model', 'glm4:cloud');

        // 1. Start scan → get scan_id
        const startRes = await fetch(`${SERVER_BASE}/scan`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ target_directory: dir, llm_provider: provider,
                                      llm_model: model, file_paths: [filePath] }),
        });
        const { scan_id } = await startRes.json();

        // 2. Subscribe to SSE stream
        const url = `${SERVER_BASE}/scan/${scan_id}/stream?target_directory=${encodeURIComponent(dir)}&llm_provider=${provider}&llm_model=${model}`;
        const es  = new EventSource(url);

        es.onmessage = (evt) => {
            const event = JSON.parse(evt.data);
            if (event.event === 'stream_end') { es.close(); return; }

            // File complete → update diagnostics
            if (event.event === 'on_chain_end' && event.name?.includes('review_file')) {
                const fileResults = event.data?.output?.file_results ?? [];
                for (const result of fileResults) {
                    dm.applyFindings(result);
                }
            }
        };

        es.onerror = () => {
            es.close();
            dm.clearScanning(filePath);
        };
    }
}
```

### 10.4 Diagnostics Manager (`vscode-ethics-agent/src/diagnostics.ts`)

```typescript
import * as vscode from 'vscode';

const SEVERITY_MAP: Record<string, vscode.DiagnosticSeverity> = {
    HIGH:   vscode.DiagnosticSeverity.Error,
    MEDIUM: vscode.DiagnosticSeverity.Warning,
    LOW:    vscode.DiagnosticSeverity.Hint,
};

export class DiagnosticsManager implements vscode.Disposable {
    private collection = vscode.languages.createDiagnosticCollection('ethics-agent');
    private scanDecoration = vscode.window.createTextEditorDecorationType({
        after: { contentText: ' ⟳ Ethics scan…', color: '#888888' },
    });
    private failDecoration = vscode.window.createTextEditorDecorationType({
        after:           { contentText: ' ✗ FAILED', color: '#FF4444', fontWeight: 'bold' },
        backgroundColor: 'rgba(255, 68, 68, 0.08)',
        border:          '1px solid rgba(255,68,68,0.3)',
        borderRadius:    '3px',
    });

    setScanning(filePath: string) {
        const editor = this.editorFor(filePath);
        if (!editor) return;
        const lastLine = editor.document.lineCount - 1;
        editor.setDecorations(this.scanDecoration, [
            new vscode.Range(lastLine, 0, lastLine, 0)
        ]);
    }

    clearScanning(filePath: string) {
        const editor = this.editorFor(filePath);
        editor?.setDecorations(this.scanDecoration, []);
    }

    applyFindings(result: any) {
        const uri         = vscode.Uri.file(result.file_path);
        const diagnostics: vscode.Diagnostic[] = [];
        const failRanges:  vscode.Range[]       = [];

        for (const finding of result.findings ?? []) {
            const startLine = Math.max(0, (finding.start_line ?? 1) - 1);
            const endLine   = Math.max(startLine, (finding.end_line ?? finding.start_line ?? 1) - 1);
            const range     = new vscode.Range(startLine, 0, endLine, Number.MAX_SAFE_INTEGER);

            const diag = new vscode.Diagnostic(
                range,
                `[${finding.regulation_name}] ${finding.explanation}`,
                SEVERITY_MAP[finding.severity] ?? vscode.DiagnosticSeverity.Warning,
            );
            diag.source = 'AI Ethics Agent';
            // Remedy shown as related information (expands on click)
            diag.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    `Remedy: ${finding.remedy}`,
                ),
            ];
            diagnostics.push(diag);

            if (finding.severity === 'HIGH') {
                failRanges.push(range);
            }
        }

        this.collection.set(uri, diagnostics);

        // Apply red inline decorations for HIGH findings
        const editor = this.editorFor(result.file_path);
        if (editor) {
            editor.setDecorations(this.failDecoration, failRanges);
            editor.setDecorations(this.scanDecoration, []);
        }
    }

    private editorFor(filePath: string): vscode.TextEditor | undefined {
        return vscode.window.visibleTextEditors.find(
            e => e.document.uri.fsPath === filePath
        );
    }

    dispose() {
        this.collection.dispose();
        this.scanDecoration.dispose();
        this.failDecoration.dispose();
    }
}
```

### 10.5 Extension Manifest (`vscode-ethics-agent/package.json`)

```json
{
  "name": "vscode-ethics-agent",
  "displayName": "AI Ethics Compliance Agent",
  "description": "Real-time AI ethics compliance checking inline in your editor",
  "version": "0.1.0",
  "engines": { "vscode": "^1.85.0" },
  "categories": ["Linters"],
  "activationEvents": ["onStartupFinished"],
  "main": "./out/extension.js",
  "contributes": {
    "configuration": {
      "title": "AI Ethics Agent",
      "properties": {
        "ethicsAgent.serverUrl":  { "type": "string",  "default": "http://localhost:8765", "description": "URL of the local ethics agent server" },
        "ethicsAgent.provider":   { "type": "string",  "default": "ollama_cloud",          "description": "LLM provider" },
        "ethicsAgent.model":      { "type": "string",  "default": "glm4:cloud",            "description": "LLM model" },
        "ethicsAgent.debounceMs": { "type": "number",  "default": 5000,                    "description": "Milliseconds to wait after last change before scanning" },
        "ethicsAgent.enabled":    { "type": "boolean", "default": true,                    "description": "Enable/disable real-time scanning" }
      }
    },
    "commands": [
      { "command": "ethicsAgent.scanNow",    "title": "Ethics Agent: Scan Current File Now" },
      { "command": "ethicsAgent.clearAll",   "title": "Ethics Agent: Clear All Diagnostics"  },
      { "command": "ethicsAgent.startServer","title": "Ethics Agent: Start Local Server"      }
    ]
  },
  "scripts": {
    "compile": "tsc -p ./",
    "watch":   "tsc -watch -p ./"
  },
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "@types/node":   "^20.0.0",
    "typescript":    "^5.3.0"
  }
}
```

### 10.6 Inline Diagnostic UX — Behaviour Specification

| Trigger                     | Behaviour                                                                                         |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| User types in supported file | 5 s debounce resets on every keystroke                                                           |
| Debounce expires            | `⟳ Ethics scan…` text appears after the cursor's last line; backend scan fires                   |
| `on_chain_start:review_file`| File row in status bar shows SCANNING                                                             |
| `on_chat_model_stream`      | Status bar progress indicator pulses                                                              |
| `on_chain_end:review_file`  | Diagnostics applied immediately — no waiting for `write_reports`                                 |
| `HIGH` finding              | Red `✗ FAILED — <short explanation>` decoration after the relevant line(s); red squiggle in gutter|
| `MEDIUM` finding            | Yellow warning squiggle; no line decoration                                                       |
| Hover over squiggle         | Tooltip: `[RegulationName] <explanation>` + `Remedy: <remedy>`                                   |
| Problem panel               | All findings listed with file, line, severity, message                                           |
| `stream_end`                | Scanning decoration cleared; final decorations frozen                                            |
| File saved clean            | All decorations and diagnostics cleared for that file                                             |

### 10.7 Server Lifecycle Management

The extension auto-starts the Python server on activation if it is not already running:

```typescript
// From extension.ts activate()
import { startServer, isServerRunning } from './server';

if (!(await isServerRunning(SERVER_BASE))) {
    await startServer(context.extensionPath);
    // Wait up to 10 s for server to be ready
    await waitForServer(SERVER_BASE, 10_000);
}
```

```typescript
// server.ts
import { spawn } from 'child_process';
import * as path from 'path';

export function startServer(extPath: string): Promise<void> {
    return new Promise((resolve) => {
        const proc = spawn('python', ['-m', 'ethics_agent.server', '--port', '8765'], {
            cwd:      extPath,
            detached: true,
            stdio:    'ignore',
        });
        proc.unref();
        setTimeout(resolve, 1500);
    });
}

export async function isServerRunning(base: string): Promise<boolean> {
    try {
        const res = await fetch(`${base}/health`);
        return res.ok;
    } catch {
        return false;
    }
}
```

---

## 11. Report Specification

Reports are written to `{target_directory}/compliance-analysis/`.

### 11.1 Per-File Report (`{filename}_analysis_report.md`)

```markdown
# Ethics Compliance Report — {filename}

**Status:** FAIL | PASS | WARN | ERROR
**Scanned:** {timestamp}
**Language:** {language}

## Summary
{summary}

## Findings ({n} total)

### Finding 1 — HIGH — {regulation_name}
- **Lines:** {start_line}–{end_line}
- **Jurisdiction:** {jurisdiction}
- **Explanation:** {explanation}
- **Remedy:** {remedy}
- **RAG Source:** Chunk {rag_chunk_id}
```

### 11.2 Consolidated Report (`final_compliance_report.md`)

```markdown
# AI Ethics Compliance — Final Report

**Scan ID:** {thread_id}
**Scanned:** {timestamp}
**Target:** {target_directory}

## Summary Table

| File            | Status | Findings |
|-----------------|--------|----------|
| main.py         | FAIL   | 3        |
| config.yaml     | PASS   | 0        |

## Critical Violations (HIGH severity)
...per-file breakdown of HIGH findings with lines and remedies...

## Full Findings by File
...
```

---

## 12. Project Directory Structure

```
ethics_agent/
│
├── server/
│   └── main.py                     # FastAPI server — POST /scan, GET /scan/{id}/stream
│
├── graphs/
│   ├── compliance_graph.py         # build_compliance_graph(), compile_graph()
│   └── checkpointer.py             # SqliteSaver / PostgresSaver factory
│
├── nodes/
│   ├── initialize.py
│   ├── fan_out.py
│   ├── review_file.py
│   ├── join_results.py
│   └── write_reports.py
│
├── tools/
│   ├── filesystem_tools.py         # read_file, write_file, run_bash, list_directory
│   └── rag_tool.py                 # query_rag LangChain Tool
│
├── rag/
│   ├── ingestor.py
│   └── retriever.py
│
├── llm/
│   └── provider_factory.py
│
├── models/
│   └── state.py                   # ComplianceState, FileResult, Finding, ProgressEvent
│
├── tracing/
│   └── langsmith_setup.py
│
├── prompts/
│   ├── loader.py
│   ├── file_reviewer.md
│   └── report_writer.md
│
├── templates/
│   └── report.html.j2             # Optional HTML report template
│
├── scripts/
│   ├── ingest_knowledge_base.py
│   └── verify_demo_scan.py
│
├── knowledge/
│   └── ai_ethics_knowledge_base.pdf
│
├── tests/
│   ├── test_graph.py
│   ├── test_nodes.py
│   └── test_tools.py
│
├── config.yaml
├── config_loader.py
├── requirements.txt
├── .env.example
│
└── vscode-ethics-agent/           # VS Code Extension (TypeScript)
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── extension.ts           # activate(), deactivate(), debounce logic
        ├── client.ts              # EthicsAgentClient — HTTP + SSE
        ├── diagnostics.ts         # DiagnosticsManager — decorations + diagnostic collection
        └── server.ts              # Server lifecycle: startServer(), isServerRunning()
```

---

## 13. Configuration Reference

### `config.yaml`

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
      models: [anthropic/claude-3.5-sonnet, openai/gpt-4o]
    groq:
      models: [llama-3.3-70b-versatile, mixtral-8x7b-32768]
    ollama_local:
      base_url: http://localhost:11434
      models: []

rag:
  knowledge_base_pdf: knowledge/ai_ethics_knowledge_base.pdf
  chroma_persist_dir: .chroma_db
  collection_name: ai_ethics_kb
  chunk_size: 800
  chunk_overlap: 100
  top_k: 5
  embedding_model: all-MiniLM-L6-v2

scan:
  max_concurrency: 6
  output_dir: compliance-analysis
  max_file_size_mb: 50
  skip_extensions: [.png, .jpg, .jpeg, .gif, .bmp, .mp4, .mp3, .zip, .tar, .gz, .whl, .pyc]

server:
  host: 127.0.0.1
  port: 8765

checkpoint:
  backend: sqlite
  sqlite_path: .langgraph_checkpoints.db

langsmith:
  project: ai-ethics-compliance-agent
  tracing_v2: true
```

### `.env.example`

```
OLLAMA_CLOUD_API_KEY=your_key
OPENROUTER_API_KEY=your_key
GROQ_API_KEY=your_key

LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=ai-ethics-compliance-agent
LANGSMITH_TRACING_V2=true

CHECKPOINT_BACKEND=sqlite
CHECKPOINT_DB_PATH=.langgraph_checkpoints.db
```

---

## 14. Python Dependencies

```
# LangGraph + LangChain
langgraph>=0.2.0
langgraph-checkpoint-sqlite>=0.1.0
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

# API Server
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sse-starlette>=1.8.0

# Filesystem Robustness
filelock>=3.14.0
chardet>=5.2.0
python-magic>=0.4.27
tenacity>=8.2.0

# Config & Utils
python-dotenv>=1.0.0
pyyaml>=6.0.0
jinja2>=3.1.0
```

> **Removed from v3.0:** `streamlit`, `tavily-python`, `duckduckgo-search`, `pandas`, `python-docx`

---

## 15. End-to-End Data Flow

```
User writes code in VS Code
 │
 ├─1─► onDidChangeTextDocument fires on every keystroke
 │       └─ debounce timer resets to T+5s
 │
 ├─2─► [T+5s] Debounce expires — isAtEnd check passes
 │       └─ EthicsAgentClient.scanFile(filePath, content)
 │          POST /scan → { scan_id }
 │          SSE connect → GET /scan/{id}/stream
 │
 ├─3─► DiagnosticsManager.setScanning() → "⟳ Ethics scan…" decoration
 │
 ├─4─► FastAPI server: graph.astream_events(initial_state, config)
 │
 ├─5─► Graph: START → initialize
 │       └─ validate dir, mkdir compliance-analysis/
 │
 ├─6─► Graph: fan_out
 │       └─ list_directory_robust → filter → [Send("review_file", ...)]
 │
 ├─7─► Graph: review_file × N (parallel)
 │       └─ For each file:
 │          astream_events emits: on_chain_start → review_file
 │          ReAct agent: read_file → classify → query_rag → reason → findings
 │          astream_events emits: on_chat_model_stream (tokens)
 │          astream_events emits: on_chain_end → review_file (FileResult)
 │
 ├─8─► VS Code: on_chain_end:review_file received
 │       └─ DiagnosticsManager.applyFindings(result)
 │          HIGH → red ✗ FAILED decoration + Error diagnostic
 │          MEDIUM → Warning diagnostic
 │          LOW → Hint diagnostic
 │          Hover = explanation + remedy
 │
 ├─9─► Graph: join_results (barrier) → write_reports
 │       └─ final_compliance_report.md written to compliance-analysis/
 │
 ├─10► SSE: stream_end event
 │       └─ EventSource closed
 │          Scanning decoration cleared
 │          Diagnostics frozen
 │
 └─11► User hovers over red squiggle
         └─ Tooltip: "[Regulation] Explanation \n Remedy: ..."
            Problems panel: full list of findings
```

---

## 16. Acceptance Criteria

| ID    | Criterion                                                                                        | Verification                                              |
|-------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| AC-01 | Python server starts on `python -m ethics_agent.server` with no errors                          | `curl localhost:8765/health` → `{"status":"ok"}`         |
| AC-02 | RAG auto-ingested on first server start; chunk count > 0                                         | Server logs show "✓ Ingested N chunks"                   |
| AC-03 | VS Code extension activates without errors; server auto-started if not running                   | Extension Output panel shows no errors                    |
| AC-04 | Typing in a Python file triggers scan after 5 s of inactivity                                   | Watch status bar decoration appear after pause            |
| AC-05 | `⟳ Ethics scan…` decoration appears beside last line of active file during scan                  | Visual observation                                        |
| AC-06 | `✗ FAILED` red decoration appears beside lines with HIGH violations                              | Open a known-bad file; verify decoration                  |
| AC-07 | Hover over red squiggle shows explanation + remedy text                                          | Visual observation                                        |
| AC-08 | Diagnostics appear in VS Code Problems panel with file, line, severity                           | Open Problems panel                                       |
| AC-09 | All 4 LLM providers selectable via VS Code settings / `config.yaml`                              | Change provider; scan; observe LangSmith span tag         |
| AC-10 | Scanning a 10-file directory completes in < 5 min on Ollama Cloud default                        | Timed test                                                |
| AC-11 | Per-file reports written to `compliance-analysis/`                                               | `ls compliance-analysis/`                                 |
| AC-12 | `final_compliance_report.md` generated and non-empty                                             | File size check                                           |
| AC-13 | Known violation in seeded test file is flagged with regulation name                              | Manual review of diagnostics                              |
| AC-14 | LangGraph `astream_events` delivers `on_chain_end:review_file` before `stream_end`              | Log timestamps from SSE stream                            |
| AC-15 | LangSmith trace created for every scan run                                                       | Open LangSmith project dashboard                          |
| AC-16 | Interrupted scan resumes from checkpoint when same `thread_id` is reused                        | Kill server mid-scan; restart; reinvoke same thread_id    |
| AC-17 | Concurrent file reviews do not corrupt `file_results` state                                      | 20-file scan; verify no duplicates in report              |
| AC-18 | Extension does not scan unsupported file types (images, binaries)                                | Open .png; verify no scan fires                           |
| AC-19 | `_safe_path()` rejects path traversal inputs                                                     | Unit test: `read_file("../../etc/passwd")` → ValueError   |
| AC-20 | Extension remains responsive (non-blocking) while scan is in progress                            | Type during scan; verify no UI freeze                     |

---

## 17. Open Questions

| #    | Question                                                                           | Recommendation                                                                              |
|------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| OQ-1 | Should the debounce be configurable per language (longer for verbose languages)?   | Yes — expose `ethicsAgent.debounceMs` per language ID in `package.json` contributes.        |
| OQ-2 | Should single-file scans bypass `fan_out` and call `review_file` directly?         | Yes — add a `single_file` fast-path in `initialize` that populates `all_files` with one.   |
| OQ-3 | EventSource API in Node.js context of VS Code extension requires a polyfill?       | Use `eventsource` npm package or switch to `fetch` with `ReadableStream` for SSE parsing.   |
| OQ-4 | Should `compliance-analysis/` reports be written for transient single-file scans? | Make it opt-in via `ethicsAgent.writeReports` setting.                                      |
| OQ-5 | Should `SqliteSaver` WAL mode be enabled for better concurrent write performance?  | Yes — set `PRAGMA journal_mode=WAL` at server startup.                                      |
| OQ-6 | LangSmith tracing optional if `LANGSMITH_API_KEY` absent?                         | Yes — skip callback if key absent; `@traceable` decorators are no-ops without the key.      |

---

## 18. Revision History

| Version | Date       | Author | Changes                                                                                       |
|---------|------------|--------|-----------------------------------------------------------------------------------------------|
| v1.0    | 2026-03-30 | —      | Initial CrewAI / Textual design                                                               |
| v2.0    | 2026-03-31 | —      | Migrated to LangGraph; Streamlit UI added; RAG integrated                                    |
| v3.0    | 2026-04-01 | —      | Full LangSmith tracing; LangGraph Send fan-out; validate_data_source subgraph; checkpointing |
| v4.0    | 2026-04-02 | —      | **Streamlit UI removed**; graph simplified (no validate_data_source); **LangGraph streaming enabled**; **VS Code extension promoted to primary deliverable** with real-time inline diagnostics |
