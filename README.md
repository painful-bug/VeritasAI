# AI Ethics Compliance Agent

A LangGraph-based compliance scanner for mixed repositories, documents, and datasets. The system reviews files, validates referenced data sources, queries an internal ethics knowledge base, and writes per-file plus consolidated reports under `compliance-analysis/`.

## Prerequisites

- Python 3.10+
- `knowledge/ai_ethics_knowledge_base.pdf`
- Optional provider keys in `.env`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
streamlit run app.py
```

The UI lets you:

- choose the configured LLM provider/model
- start or resume a scan from LangGraph checkpoints
- inspect live scan progress and logs
- rebuild/query the RAG knowledge base
- view and download the final Markdown or HTML report

## Notes

- The implementation keeps your configured default provider/model intact.
- If an LLM or web-search dependency is unavailable, the scanner falls back to deterministic heuristics instead of failing the whole run.
- Reports are written atomically to `compliance-analysis/` inside the scanned directory.
