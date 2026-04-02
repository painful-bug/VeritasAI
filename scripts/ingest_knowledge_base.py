#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("LANGSMITH_TRACING_V2", "false")

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

from config_loader import load_config
from rag.ingestor import ingest
from rag.retriever import Retriever

DEFAULT_PROBE_QUERY = "automated hiring decision system using demographic attributes including gender age"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest the AI ethics knowledge-base PDF into ChromaDB.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--probe-query", default=DEFAULT_PROBE_QUERY)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()
    config = load_config(args.config)
    count = ingest(config)
    print(f"✓ Ingested {count} chunks into ChromaDB")

    retriever = Retriever.get_instance(config)
    hits = retriever.query(args.probe_query, top_k=args.top_k)
    if not hits:
        print("Retrieval probe returned no hits after ingestion.", file=sys.stderr)
        return 2

    for index, hit in enumerate(hits, start=1):
        metadata = hit.get("metadata", {}) or {}
        excerpt = " ".join(str(hit.get("text", "")).split())[:220]
        print(f"{index}. chunk={metadata.get('chunk_id', 'n/a')} page={metadata.get('page', 'n/a')} score={hit.get('score')}")
        print(f"   {excerpt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
