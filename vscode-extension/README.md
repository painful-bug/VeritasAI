# VS Code Extension Runbook

This package is the VS Code frontend for the AI Ethics Compliance Agent. It starts the Python MCP server as a subprocess, sends the active file to `check_file`, and renders streamed findings as native diagnostics.

## Prerequisites

- Repository dependencies installed in the repo root:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Knowledge base ingested at least once:
  - `python scripts/ingest_knowledge_base.py`
- Extension dependencies installed:
  - `cd vscode-extension`
  - `npm install`
  - `npm run compile`

## Launch In VS Code

1. Open `vscode-extension/` in VS Code.
2. Press `F5` and choose `Run AI Ethics Extension`.
3. The launch config opens an Extension Development Host on the parent repo so the extension can analyze real files in this repository.

## Configure The Extension Host

In the Extension Development Host, open Settings and set:

- `AI Ethics: Python Path` -> absolute path to the repo venv Python, for example:
  - `/Users/aishik/Documents/Programming/ethics_agent/.venv/bin/python`
- `AI Ethics: Server Path` -> leave empty if the workspace is the repo root or `vscode-extension/`
  - the extension now auto-detects `mcp_server.py` by walking upward from the active file and workspace folders
- `AI Ethics: Provider` -> one of `ollama_cloud`, `openrouter`, `groq`, `ollama_local`
- `AI Ethics: Model` -> a model valid for the selected provider

Provider setup now matters for supported-file reviews. The published extension does not ship any publisher API keys. Users bring their own keys, the extension stores them in VS Code SecretStorage, and it injects them into the Python MCP subprocess only at runtime. If the backend cannot create the configured LLM client or the model fails to return valid review JSON, the scan result is surfaced as an explicit `ERROR`.

## Bring Your Own Keys

Use the Command Palette:

- `AI Ethics: Set API Key` to store a provider key in VS Code SecretStorage
- `AI Ethics: Remove API Key` to delete a stored key
- `AI Ethics: Open Setup` to open the guided setup flow

The extension prompts on activation or before scanning if the selected remote provider needs a key and none is configured.

## End-to-End Test

1. In the Extension Development Host, open:
   - `demo_violations/unsafe_hiring_fixture/unsafe_hiring_screen.py`
2. Wait at least 5 seconds without typing.
3. Confirm all of the following:
   - the status bar changes to `AI Ethics: Analysing...`
   - the `AI Ethics` output channel logs a connection line and a check line
   - the Problems panel shows `AI Ethics` findings
   - red/yellow/blue diagnostics appear inline in the editor
   - `compliance-analysis/unsafe_hiring_screen_analysis_report.md` is written in the repo root

## Manual Trigger

Use the Command Palette and run `AI Ethics: Scan Current File` to trigger an immediate full-file compliance check for the active editor without waiting for the debounce timer.

## Troubleshooting

- If no diagnostics appear:
  - open `View -> Output -> AI Ethics`
  - check that the Python path points to the repo `.venv`
  - check that `mcp_server.py` resolves correctly
- If the MCP server fails on startup:
  - run `python mcp_server.py` from the repo root using the same interpreter as `AI Ethics: Python Path`
- If the extension compiles but does not activate:
  - run `npm run compile` again and relaunch the Extension Development Host
