# AI Ethics Compliance Agent

The project is now a VS Code-first AI ethics reviewer. A TypeScript extension watches the active editor, waits 5 seconds after the last change, and calls a Python LangGraph backend over MCP stdio. Findings are surfaced as native VS Code diagnostics and each completed scan writes a Markdown report under `compliance-analysis/`.

The review runtime now follows an agentic RAG pattern inspired by the attached design reference:
- local retrieval-first grounding from ChromaDB,
- self-grading (`Relevancy`, `Faithfulness`, `Context Quality`),
- conditional web augmentation when confidence/context is insufficient,
- final mapped compliance findings with retrieval and web evidence in reports.

## Prerequisites

- Python 3.10+
- Node.js 20+
- `knowledge/ai_ethics_knowledge_base.pdf`
- For local development, optional provider keys in `.env`

## Python Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/ingest_knowledge_base.py
```

## Extension Setup

```bash
cd vscode-extension
npm install
npm run compile
```

Then open `vscode-extension/` in VS Code and press `F5` with the `Run AI Ethics Extension` launch config. Use the repo venv for `aiEthics.pythonPath`. `aiEthics.serverPath` can stay empty when the workspace is the repo root or `vscode-extension/`.

Detailed extension run and test instructions are in `vscode-extension/README.md`.

For the published extension, users bring their own provider keys. The extension stores user-entered credentials in VS Code SecretStorage and injects them into the MCP backend process at runtime instead of shipping publisher keys.

## Manual Verification

```bash
python scripts/verify_demo_scan.py
python mcp_server.py
```

## Notes

- The Streamlit UI has been removed.
- Reports are written atomically to `compliance-analysis/` near the workspace root that contains the checked file.
- LangSmith tracing is optional and activates only when `LANGSMITH_API_KEY` is configured.
- Default RAG chunking is `500/50` with compliance-focused retrieval ranking and trust scoring.
- `.env` remains a local development convenience; do not commit real credentials or rely on it for Marketplace users.
