# Copilot Instructions for this Repository

## Build, test, and lint commands

### Python backend (repo root)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
pytest
```

Run a single test:

```bash
pytest tests/test_review_file_node.py::test_review_file_node_returns_actionable_error_for_missing_provider_key
```

Useful runtime checks:

```bash
python scripts/ingest_knowledge_base.py
python scripts/verify_demo_scan.py
python mcp_server.py
```

### VS Code extension (`vscode-extension/`)

```bash
npm install
npm run compile
```

Single-file TypeScript compile check:

```bash
npx tsc -p ./ --pretty false
```

### Linting

There is no dedicated lint script configured in this repository root or in `vscode-extension/package.json`.

## High-level architecture

- The product is **VS Code-first**: the extension debounces editor changes (default 5s), sends scan requests over MCP stdio, and renders findings as diagnostics.
- `vscode-extension/src/mcpClient.ts` launches `mcp_server.py` as a Python subprocess and calls MCP tools:
  - `check_file` (main scan path)
  - `refresh_directory_analysis` (bootstrap/manual refresh)
- The Python backend runs a **linear LangGraph pipeline** in `graphs/compliance_graph.py`:
  - `initialize` → `code_reviewer` → `review_file` → `write_report`
- `code_reviewer` (`nodes/review_repository.py`) generates/refreshes `DIRECTORY_ANALYSIS.md` via `analysis/repository_review.py` and injects it as repository context for later review.
- `review_file` (`nodes/review_file.py`) runs:
  1. deterministic file preparation in `analysis/core.py`
  2. LLM compliance evaluation in `analysis/llm_review.py`
  3. local RAG retrieval (ChromaDB-backed) and conditional web augmentation when grading is weak
- `write_report` writes a Markdown artifact to `compliance-analysis/<file>_analysis_report.md`.

## Key conventions and project-specific patterns

- `DIRECTORY_ANALYSIS.md` is a generated artifact that is both:
  1. **input context** for reviews
  2. **excluded from review targets** itself
- The backend enforces eligibility in `analysis/core.py`: only `source_code`, `document`, and `structured_data` are reviewable; unsupported/binary/config/media become `SKIPPED`.
- For reviewable files, LLM review is required; if provider/model/credentials fail, status is explicit `ERROR` (not silent fallback).
- Provider/model normalization happens server-side (`llm/provider_factory.py`) to tolerate stale extension settings.
- Findings from snippet scans are remapped to absolute lines using `line_offset` (`nodes/review_file.py`).
- Progress and diagnostics rely on custom streamed event names (`scan_started`, `directory_analysis_ready`, `violation_found`, `scan_complete`, etc.); keep extension/backend event contracts aligned when changing either side.
- `analysis/repository_review.py` caches directory-analysis freshness with a snapshot hash embedded in a metadata header; unchanged snapshots reuse existing analysis content.
- Reports and generated artifacts are written through filesystem safety helpers (atomic writes + locking in `tools/filesystem_tools.py`), so preserve those helpers when editing write paths.

## MCP servers to consider for Copilot sessions

- **GitHub MCP server**: useful for PR review workflows, issue triage, and GitHub Actions failure/log investigation while changing this extension/backend pair.
- **Playwright MCP server**: useful if you add browser-based docs/demo surfaces or web UI artifacts; not part of the current default runtime path.
