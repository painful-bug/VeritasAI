# Repository Guidelines

## Project Structure & Module Organization
Core scanner logic lives in `analysis/`, `nodes/`, `graphs/`, and `models/`. Integration layers live in `llm/`, `rag/`, `tools/`, `tracing/`, and `ui/`. Prompt templates are stored in `prompts/`, the HTML report template is in `templates/`, and manual utilities are in `scripts/`. Tests live under `tests/`. Keep the knowledge-base PDF at `knowledge/ai_ethics_knowledge_base.pdf`; vector data is persisted in `.chroma_db/`. Scan output is written to `compliance-analysis/` inside the scanned target, so do not hand-edit generated reports.

## Build, Test, and Development Commands
Set up the environment with `python3 -m venv .venv`, `source .venv/bin/activate`, and `pip install -r requirements.txt`. Start the UI with `streamlit run app.py`. Run the test suite with `pytest`. Rebuild the knowledge base manually with `python scripts/ingest_knowledge_base.py`. Validate the demo unsafe fixture with `python scripts/verify_demo_scan.py`.

## Coding Style & Naming Conventions
Use Python 3.10+ features, 4-space indentation, UTF-8 text, and explicit type hints where the code already expects them. Follow the existing naming pattern: `snake_case` for modules, functions, and config keys; `PascalCase` only for classes and typed models. Prefer small, composable functions and preserve deterministic fallbacks when touching LLM or RAG paths. No repository-wide formatter or linter is configured here, so match the existing style closely.

## Testing Guidelines
Write `pytest` tests in `tests/test_*.py`. Keep tests fast and deterministic; mock LLM and RAG calls instead of depending on external providers. Add targeted coverage for new rule-detection paths, report rendering, config loading, and graph/join behavior. Before opening a PR, run `pytest` and, for UI or pipeline changes, exercise at least one local scan.

## Commit & Pull Request Guidelines
This workspace snapshot does not include `.git` metadata, so no local commit-history convention can be inferred. Use short imperative commit subjects such as `Add timeout fallback for LLM review`. PRs should include the problem statement, impacted modules, config or prompt changes, test commands run, and screenshots for Streamlit UI changes. Link related issues and note any changes that affect `config.yaml`, `.env`, checkpoints, or the RAG store.
