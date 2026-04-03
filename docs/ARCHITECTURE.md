# AI Ethics Compliance Agent Architecture

## 1. System Identity

The current system is a VS Code-first, real-time AI ethics reviewer for local repositories.

It is built around five ideas:

1. The editor is the user interface.
2. The Python backend is invoked over MCP stdio, not HTTP or Streamlit.
3. Every scan is incremental and centered on the currently changed code region.
4. Every scan is repository-aware because a generated `DIRECTORY_ANALYSIS.md` is maintained and injected into later reasoning.
5. Deterministic analysis runs first, and optional LLM reasoning only enriches the result when available.

At runtime the system does not scan an entire repository on every keystroke. It scans one changed file region at a time, but it augments that region with:

- nearby previously discovered findings in the same document,
- repository-wide context from `DIRECTORY_ANALYSIS.md`,
- local regulatory evidence from ChromaDB,
- optional web augmentation when confidence is low.

That architecture produces fast editor feedback while preserving cross-file understanding.

## 2. Architecture At A Glance

```text
[Developer in VS Code]
          |
          v
[VS Code Extension (extension.ts)]
          |
          v
[MCP Client (mcpClient.ts)]
          |
          v
[mcp_server.py] -----------------------------------------> [LangSmith]
          |
          v
[LangGraph Compliance Graph] -----------------------------> [LangGraph Checkpointer]
          |
          v
[initialize] -> [code_reviewer] -> [review_file] -> [write_report] -> [Markdown Report (compliance-analysis)]
                  |
                  v
[Repository Analysis (analysis/repository_review.py)] -> [DIRECTORY_ANALYSIS.md]

[review_file] -> [Deterministic Analysis (analysis/core.py)]
[review_file] -> [LLM Enrichment (analysis/llm_review.py)] -> [Retriever (rag/retriever.py)]
[LLM Enrichment (analysis/llm_review.py)] -- conditional --> [Web Search Tool]
[review_file] ---------------------------------------------> [LangSmith]
```

## 3. Design Principles

### 3.1 Incremental By Default

The extension does not send the full file on every edit. It tracks a changed line window, waits for inactivity, extracts a snippet, and sends only that region plus a line offset so findings can be remapped to absolute file lines.

### 3.2 LLM-First Review

`analysis/core.py` now prepares file eligibility, structural summaries, and predicted outputs. Actual compliance judgement for supported files is produced by the LLM review layer, not by heuristic rules in `core.py`.

### 3.3 Repository-Aware Reasoning

The `code_reviewer` stage creates and maintains `DIRECTORY_ANALYSIS.md`. That file is agent-generated context and is never itself treated as a review target.

### 3.4 Retrieval-Grounded Judgement

Compliance claims are expected to be grounded in local RAG evidence first. Web search is optional and only used when relevancy or context quality is weak.

### 3.5 Safe Degradation

If RAG ingestion is unavailable, the system continues. If the configured provider/model is stale, the backend normalizes it to a valid configured fallback. If repository analysis fails, file review still proceeds without that extra context.

## 4. Runtime Boundary

### 4.1 What The System Reviews

Only these file classes are treated as compliance review targets:

- `source_code`
- `document`
- `structured_data`

This is enforced in [analysis/core.py](analysis/core.py).

Representative extensions:

- Source code: `.py`, `.js`, `.ts`, `.tsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.cs`, `.rb`, `.php`, `.swift`, `.kt`, `.sh`
- Documents: `.md`, `.txt`, `.rst`, `.pdf`, `.docx`, `.doc`, `.html`, `.htm`
- Structured data: `.csv`, `.tsv`, `.json`, `.jsonl`, `.yaml`, `.yml`, `.xml`

### 4.2 What The System Excludes

The architecture intentionally excludes:

- `.env` files
- virtual environments
- `node_modules`
- `.git`
- cache/build artifacts
- generated compliance reports
- generated `DIRECTORY_ANALYSIS.md`
- config-only files such as `.toml`, `.ini`, `.cfg`, `.conf`, `.properties`
- media and binary files

This exclusion matters in two places:

1. The extension refuses to schedule live scans for unsupported files.
2. The backend refuses to review unsupported files even if a caller sends them directly.

## 5. Active Components

## 5.1 VS Code Presentation Layer

Primary files:

- `vscode-extension/src/extension.ts`
- `vscode-extension/src/mcpClient.ts`
- `vscode-extension/src/diagnostics.ts`
- `vscode-extension/src/statusBar.ts`
- `vscode-extension/package.json`

Responsibilities:

- watch editor changes,
- debounce scans,
- bootstrap `DIRECTORY_ANALYSIS.md` on activation,
- exclude unsupported targets,
- send incremental scan requests to the backend,
- stream progress and violation events,
- render diagnostics inline,
- surface status in the status bar,
- expose manual commands for directory analysis creation and refresh.

Important commands:

- `aiEthics.openProblems`
- `aiEthics.showOutput`
- `aiEthics.createDirectoryAnalysis`
- `aiEthics.refreshDirectoryAnalysis`

Important runtime behaviors:

- Startup calls `refresh_directory_analysis(force=false)` to ensure `DIRECTORY_ANALYSIS.md` exists.
- Live scans only run after 5 seconds of inactivity by default.
- `DIRECTORY_ANALYSIS.md` is explicitly excluded from live scanning.
- Results are discarded if the document changed again before the scan completed.

## 5.2 MCP Bridge

Primary file:

- `mcp_server.py`

Responsibilities:

- expose backend functionality as MCP tools,
- build the initial graph state,
- normalize provider/model selection,
- stream LangGraph events back to the extension,
- translate final graph output into MCP structured content,
- emit periodic heartbeats during long scans,
- expose manual repository-analysis refresh.

Active MCP tools:

- `check_file`
- `refresh_directory_analysis`

`check_file` is the main real-time scan entrypoint. `refresh_directory_analysis` is used by startup bootstrap and manual refresh commands.

## 5.3 Orchestration Layer

Primary files:

- `graphs/compliance_graph.py`
- `graphs/checkpointer.py`
- `models/state.py`
- `models/events.py`

The active graph is linear:

```text
[START] -> [initialize] -> [code_reviewer] -> [review_file] -> [write_report] -> [END]
```

This is intentionally simple. The system no longer uses the older multi-node fan-out pipeline described in earlier documents. The graph now models one compliance check for one file/snippet at a time.

`graphs/checkpointer.py` provides:

- SQLite checkpointing by default,
- optional Postgres checkpointing,
- persistent thread ids for resumability or audit.

## 5.4 Repository Context Builder

Primary file:

- `analysis/repository_review.py`

Logical role:

- `code_reviewer`

This stage is the repository-wide analyzer the user requested. It is called `code_reviewer` in the LangGraph topology, but its implementation is deterministic rather than a separate tool-calling LLM agent.

Responsibilities:

- resolve the workspace root,
- walk the repository recursively,
- apply exclusion rules,
- consider only reviewable file classes,
- infer per-file type, language, symbols, schema hints, local references, and predicted role,
- build directory summaries and cross-file relationships,
- write `DIRECTORY_ANALYSIS.md`,
- cache a snapshot hash in an HTML comment header,
- reuse the previous file when the repository has not changed,
- update automatically when files are added, removed, or modified.

Generated artifact:

- `DIRECTORY_ANALYSIS.md` in the workspace root

Key design detail:

`DIRECTORY_ANALYSIS.md` is both output and input. It is produced by the backend for its own future use, but it is never treated as codebase source material to review.

## 5.5 File Preparation Layer

Primary file:

- `analysis/core.py`

Responsibilities:

- classify the file,
- skip unsupported targets,
- extract schema hints,
- detect local and external data sources,
- identify sensitive fields,
- build a prepared `FileResult` shell for the LLM,
- generate a human-readable summary,
- infer likely real-world output of the code or file.

Important behaviors:

- This layer does not make the final compliance decision for supported files.
- Review eligibility is enforced here, not only in the extension.
- `DIRECTORY_ANALYSIS.md` is skipped as an agent-generated artifact.
- Config/media/binary files are skipped.

This layer is the structural context builder that feeds the LLM review path.

## 5.6 LLM Review Layer

Primary files:

- `nodes/review_file.py`
- `analysis/llm_review.py`
- `analysis/agentic_runtime.py`
- `llm/provider_factory.py`

Responsibilities:

- create the active LLM client for the configured provider,
- combine prepared file metadata with nearby reviewed context and repository context,
- retrieve regulatory grounding from ChromaDB,
- self-grade the quality of the answer,
- optionally augment with web search,
- map LLM output into the strict `FileResult` contract,
- emit retrieval evidence and web evidence for later reporting.

This layer has two paths:

1. Standard LangChain model invocation through `ChatOpenAI`, `ChatGroq`, or `ChatOllama`
2. Optional `pydantic_ai` route for Groq-backed tool-using review

The active file review node:

- prepares metadata in `analysis/core.py`,
- requires the LLM path for supported-file compliance decisions,
- returns `ERROR` if the file is reviewable but the LLM cannot be created or cannot return valid review JSON,
- remaps findings back to absolute lines with `line_offset`.

## 5.7 Retrieval Layer

Primary files:

- `rag/retriever.py`
- `rag/ingestor.py`
- `rag/storage.py`

Responsibilities:

- maintain the ChromaDB-backed knowledge store,
- embed and retrieve chunks from `knowledge/ai_ethics_knowledge_base.pdf`,
- expand compliance queries,
- compute confidence and trust scores,
- deduplicate retrieved evidence,
- serve top-ranked regulatory context to LLM review.

Important design choices:

- Retrieval is local-first.
- Query expansion is domain-specific.
- Trust scoring combines embedding distance, query overlap, regulatory vocabulary, and metadata quality.
- If the collection is unavailable, retrieval gracefully returns no hits.

## 5.8 Reporting Layer

Primary files:

- `nodes/write_report.py`
- `analysis/reports.py`

Responsibilities:

- resolve the workspace output directory,
- write one Markdown compliance report per reviewed file,
- include LLM review, retrieval, and web-evidence fields in the final artifact,
- preserve evidence provenance.

Generated report location:

- `compliance-analysis/<file>_analysis_report.md`

Reports are written atomically through `tools/filesystem_tools.py`.

## 5.9 Observability And Tracing

Primary files:

- `tracing/langsmith_setup.py`
- `models/events.py`

Responsibilities:

- attach LangSmith callbacks when enabled,
- name runs consistently,
- tag runs with provider/model metadata,
- resolve LangSmith URLs for completed scans,
- emit consistent progress events and custom events.

The LangGraph run and nested nodes are visible in LangSmith. That includes `initialize`, `code_reviewer`, `review_file`, `write_report`, and nested retrieval/model calls.

## 5.10 Filesystem Safety Layer

Primary file:

- `tools/filesystem_tools.py`

Responsibilities:

- safe path resolution,
- binary detection,
- retrying text reads,
- atomic writes via temp file + move,
- file locks for report and artifact generation.

This layer is why generated artifacts such as reports and `DIRECTORY_ANALYSIS.md` can be updated safely even while the extension is active.

## 6. Data Contracts

The central runtime contract is `ComplianceState` in `models/state.py`.

Important state fields:

- `file_path`: absolute target path
- `file_content`: snippet or full content under review
- `llm_provider`: normalized provider name
- `llm_model`: normalized model name
- `line_offset`: offset used to convert snippet-relative findings to absolute lines
- `reviewed_context`: nearby prior findings from the same editor document
- `agentic_context`: repository-wide `DIRECTORY_ANALYSIS.md` content
- `directory_analysis_path`: path of the generated repository context artifact
- `workspace_root`: resolved repository root
- `file_result`: final result for this check
- `progress_events`: additive timeline payloads
- `final_report_md`: rendered report content
- `langsmith_run_id`, `langsmith_run_url`: tracing metadata

The final per-file output contract is `FileResult`.

Important `FileResult` fields:

- `status`
- `summary`
- `predicted_output`
- `findings`
- `agentic_grade`
- `retrieval_evidence`
- `web_search_evidence`
- `report_path`

## 7. Repository Analysis Lifecycle

```text
[Activation or scan request]
         |
         v
[Resolve workspace root]
         |
         v
[Does DIRECTORY_ANALYSIS.md exist?]
    | Yes                             | No
    v                                 v
[Compute snapshot hash]       [Walk repository recursively]
    |
    v
[Hash changed?]
   | No                        | Yes
   v                           v
[Load existing DIRECTORY_ANALYSIS.md]    [Walk repository recursively]
            \                    /
             \                  /
              v                v
[Analyse only source_code, document, structured_data]
         |
         v
[Build directory summaries, file summaries, relationships]
         |
         v
[Write DIRECTORY_ANALYSIS.md with metadata header]
         |
         v
[Inject markdown into later file reviews]
```

Important lifecycle triggers:

- automatic startup bootstrap from the extension,
- automatic refresh during the `code_reviewer` node,
- manual refresh via VS Code command.

Important invariants:

- the file is created once when absent,
- reused when the repository snapshot has not changed,
- regenerated when the repository changes,
- excluded from subsequent review targets.

## 8. Real-Time Startup Flow

```text
User -> VS Code Host: Open workspace
VS Code Host -> Extension: activate()
Extension -> MCP Client: connect over stdio
Extension -> mcp_server.py: refresh_directory_analysis(force=false)
mcp_server.py -> repository_review.py: ensure_directory_analysis()
repository_review.py -> mcp_server.py: existing or newly written DIRECTORY_ANALYSIS.md
mcp_server.py -> Extension: structured result + progress
Extension -> User: output log and optional open document
```

Startup is not a compliance scan. It is a repository-context bootstrap.

## 9. Real-Time Edit Execution Flow

```text
User -> VS Code Extension: Edit supported file
VS Code Extension -> VS Code Extension: Merge changed window and debounce
VS Code Extension -> VS Code Extension: Build snippet + reviewed_context
VS Code Extension -> MCP Client: check_file(file_path, snippet, line_offset, reviewed_context, provider, model)
MCP Client -> MCP Server: stdio tool request
MCP Server -> MCP Server: normalize provider/model
MCP Server -> LangGraph: start ComplianceCheck
LangGraph -> code_reviewer: ensure DIRECTORY_ANALYSIS.md exists and is current
code_reviewer -> LangGraph: agentic_context + analysis path
LangGraph -> review_file: review snippet
review_file -> analysis/core.py: prepare file metadata and eligibility
review_file -> analysis/llm_review.py: perform repository-aware LLM compliance review
analysis/llm_review.py -> rag/retriever.py: retrieve local regulatory evidence
analysis/llm_review.py -> analysis/llm_review.py: self-grade relevancy / faithfulness / context quality

If context is insufficient:
analysis/llm_review.py -> web_search_tool: optional web search
web_search_tool -> analysis/llm_review.py: external context

analysis/llm_review.py -> review_file: enriched FileResult
review_file -> MCP Client: violation_found / progress events
LangGraph -> write_report: write Markdown report
write_report -> MCP Client: final result
MCP Client -> VS Code Extension: scan_complete + structured output
VS Code Extension -> User: diagnostics, status bar, output log
```

## 10. Detailed Node Behavior

## 10.1 `initialize`

File:

- `nodes/initialize.py`

Purpose:

- resolve the output directory relative to the current file,
- ensure the report directory exists,
- emit a `scan_started` progress event.

This node does not inspect code. It establishes the filesystem context for the rest of the run.

## 10.2 `code_reviewer`

File:

- `nodes/review_repository.py`

Purpose:

- guarantee availability of repository context,
- emit repository-analysis progress and readiness events,
- store the repository markdown in `agentic_context`.

Failure semantics:

- if repository analysis fails, the node returns blank context,
- later file review still proceeds.

## 10.3 `review_file`

File:

- `nodes/review_file.py`

Purpose:

- perform the actual compliance review for the current file/snippet.

Execution order:

1. Emit `file_started`
2. Prepare file metadata and enforce skip rules
3. Create an LLM client unless review is disabled or the file was skipped
4. Run RAG-first repository-aware LLM review
5. Apply snippet line offsets
6. Emit `agentic_grade`, retrieval, and web events
7. Emit one `violation_found` event per finding
8. Emit `file_complete`

This node is the center of runtime behaviour.

## 10.4 `write_report`

File:

- `nodes/write_report.py`

Purpose:

- build final Markdown for the current file,
- write it atomically to `compliance-analysis`,
- attach `report_path` to the final result.

This node closes the loop between live diagnostics and durable artifacts.

## 11. Context Assembly Model

The LLM does not reason over the snippet in isolation. The context stack is layered in this order:

```text
[Changed snippet]
    |
    v
[Prepared file summary]
    |
    v
[Nearby reviewed_context]
    |
    v
[Repository-wide DIRECTORY_ANALYSIS.md]
    |
    v
[Local RAG excerpts]
    |
    v
[Conditional web excerpts]
    |
    v
[Final FileResult]
```

Interpretation:

- The snippet gives local syntax and lines.
- The prepared file summary anchors the first interpretation.
- Nearby reviewed context preserves continuity across repeated edits.
- `DIRECTORY_ANALYSIS.md` supplies cross-file intent and repository purpose.
- RAG adds regulatory grounding.
- Web is only used when needed.

## 12. Provider And Model Resolution

Provider/model selection is intentionally normalized before model creation.

Primary file:

- `llm/provider_factory.py`

Responsibilities:

- map provider to backend adapter,
- maintain a cache of instantiated LLMs,
- enumerate configured models,
- normalize stale or invalid provider/model selections,
- fall back to a valid configured model when the requested one is unavailable.

This is important because the extension can hold a stale saved model value. The backend now resolves that mismatch before any OpenRouter or OpenAI-compatible request is made.

## 13. Progress, Events, And Diagnostics

The system emits two classes of runtime signals:

1. additive progress events stored in graph state
2. custom LangChain events streamed immediately through MCP

Important streamed events:

- `scan_started`
- `directory_analysis_started`
- `directory_analysis_ready`
- `file_started`
- `agentic_grade`
- `agentic_retrieval`
- `agentic_web_search`
- `violation_found`
- `file_complete`
- `scan_complete`

The extension consumes those events to:

- update status bar state,
- add diagnostics before the final result arrives,
- keep the output panel informative during long-running scans.

`vscode-extension/src/diagnostics.ts` maps compliance severities to native VS Code severities and attaches remedies as related information.

## 14. Generated Artifacts

Generated files and stores:

- `DIRECTORY_ANALYSIS.md`
- `compliance-analysis/*.md`
- `.langgraph_checkpoints.db`
- `.chroma_db/`

Artifact rules:

- `DIRECTORY_ANALYSIS.md` is generated for context, not reviewed as source material.
- `compliance-analysis/` is output, not repository input.
- checkpoint and vector stores are operational state, not review targets.

## 15. Failure Handling And Fallbacks

### 15.1 Unsupported Target

If the file is not source code, a document, or structured data, the result is `SKIPPED`.

### 15.2 Repository Analysis Failure

If `DIRECTORY_ANALYSIS.md` cannot be built, `code_reviewer` returns empty context and scan execution continues.

### 15.3 RAG Failure

If ingestion or collection initialization fails, the system continues without retrieval evidence.

### 15.4 LLM Failure

If provider initialization fails or invocation raises, the result becomes `ERROR` for supported files rather than silently downgrading to a heuristic-only review.

### 15.5 Stale Editor State

If the document changed while a scan was in flight, the extension discards the stale result instead of surfacing it.

### 15.6 Invalid Model Configuration

If a saved provider/model pair is invalid, the backend normalizes it to a configured fallback before attempting the LLM call.

## 16. Active Runtime Files

The following files form the active runtime path:

- `vscode-extension/src/extension.ts`
- `vscode-extension/src/mcpClient.ts`
- `vscode-extension/src/diagnostics.ts`
- `vscode-extension/src/statusBar.ts`
- `mcp_server.py`
- `graphs/compliance_graph.py`
- `graphs/checkpointer.py`
- `nodes/initialize.py`
- `nodes/review_repository.py`
- `nodes/review_file.py`
- `nodes/write_report.py`
- `analysis/repository_review.py`
- `analysis/core.py`
- `analysis/llm_review.py`
- `analysis/agentic_runtime.py`
- `analysis/reports.py`
- `llm/provider_factory.py`
- `rag/retriever.py`
- `rag/ingestor.py`
- `rag/storage.py`
- `tools/filesystem_tools.py`
- `tools/web_search_tool.py`
- `models/state.py`
- `models/events.py`
- `tracing/langsmith_setup.py`
- `config_loader.py`
- `config.yaml`

## 17. Auxiliary Or Legacy Files

Some repository files exist but are not part of the active runtime path described above.

Examples:

- `graphs/file_review_subgraph.py`
- prompt assets for older or exploratory subgraph-based approaches
- older PRD documents
- demo fixtures under `demo_violations/`

These files remain useful for experimentation, tests, or documentation, but they are not the live execution path used by the VS Code extension.

## 18. Summary

The architecture is now centered on one practical workflow:

1. bootstrap repository context,
2. watch the editor,
3. scan only changed regions,
4. inject repository-wide understanding,
5. ground compliance reasoning in RAG,
6. optionally enrich with LLM and web evidence,
7. stream findings back to VS Code immediately,
8. persist a report for the reviewed file.

That combination gives the system three important properties at once:

- it feels fast in the editor,
- it remains explainable and traceable,
- it reasons with a whole-repository mental model instead of isolated snippets.
