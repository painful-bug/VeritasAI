#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Manual scripts should stay usable offline; callers can still override these
# flags in their shell before execution if they explicitly want LangSmith.
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGSMITH_TRACING_V2", "false")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

from config_loader import load_config
from rag.ingestor import ingest
from tools.rag_tool import query_rag_tool

DEFAULT_PROBE_QUERY = "automated hiring decision using demographic attributes gender age"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest the AI ethics knowledge-base PDF into the local Chroma store.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML. Default: config.yaml")
    parser.add_argument(
        "--probe-query",
        default=DEFAULT_PROBE_QUERY,
        help="Query to run after ingestion to confirm retrieval works.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieval hits to print after ingestion.")
    return parser.parse_args()


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()
    config = load_config(args.config)
    rag_config = config.get("rag", {})
    pdf_path = Path(rag_config.get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf"))

    if not pdf_path.exists():
        print(f"Knowledge base PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    print(f"PDF: {pdf_path}")
    print(f"Vector store: {rag_config.get('persist_dir', '.chroma_db')}")
    print(
        "Embedder: "
        f"{rag_config.get('embedder_provider', 'ollama')}/"
        f"{rag_config.get('embedder_model', 'nomic-embed-text:v1.5')}"
    )

    chunk_count = ingest(config)
    print(f"Ingested {chunk_count} chunks into {rag_config.get('collection_name', 'ai_ethics_kb')}.")

    hits = query_rag_tool(description=args.probe_query, top_k=args.top_k, config=config)
    if not hits:
        print("Retrieval probe returned no hits after ingestion.", file=sys.stderr)
        return 2

    print()
    print(f"Probe query: {args.probe_query}")
    for index, hit in enumerate(hits, start=1):
        metadata = hit.get("metadata", {}) or {}
        excerpt = " ".join(str(hit.get("text", "")).split())[:220]
        print(
            f"{index}. chunk={metadata.get('chunk_id', 'n/a')} "
            f"page={metadata.get('page', 'n/a')} score={hit.get('score')}"
        )
        print(f"   {excerpt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
