#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import uuid
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
from graphs.compliance_graph import compile_graph
from rag.ingestor import ingest, needs_ingestion
from rag.retriever import Retriever
from tracing.langsmith_setup import get_run_config

DEFAULT_TARGET = REPO_ROOT / "demo_violations" / "unsafe_hiring_fixture" / "unsafe_hiring_screen.py"
DEFAULT_QUERY = "automated hiring decision system using demographic attributes including gender age"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the single-file demo scan flow.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--file", default=str(DEFAULT_TARGET))
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--force-ingest", action="store_true")
    parser.add_argument("--probe-query", default=DEFAULT_QUERY)
    return parser.parse_args()


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()
    config = load_config(args.config)
    provider = args.provider or config.get("llm", {}).get("default_provider", "ollama_cloud")
    model = args.model or config.get("llm", {}).get("default_model", "glm4:cloud")
    file_path = Path(args.file).expanduser().resolve()

    if not file_path.exists():
        print(f"File does not exist: {file_path}", file=sys.stderr)
        return 1

    if args.force_ingest or needs_ingestion(config):
        count = ingest(config)
        print(f"✓ Ingested {count} chunks into ChromaDB")

    probe_hits = Retriever.get_instance(config).query(args.probe_query, top_k=3)
    if not probe_hits:
        print("Probe query returned no RAG hits.", file=sys.stderr)
        return 2

    graph = compile_graph(config=config)
    initial_state = {
        "file_path": str(file_path),
        "file_content": file_path.read_text(encoding="utf-8"),
        "llm_provider": provider,
        "llm_model": model,
        "config": config,
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }
    thread_id = str(uuid.uuid4())
    result = graph.invoke(initial_state, config=get_run_config(thread_id, str(file_path), provider, model))
    file_result = result.get("file_result")
    if not file_result:
        print("Graph did not return a file_result.", file=sys.stderr)
        return 3

    print(f"Status: {file_result['status']}")
    print(f"Summary: {file_result['summary']}")
    for finding in file_result.get("findings", []):
        print(f"- [{finding['severity']}] {finding['regulation_name']}")
        print(f"  {finding['explanation']}")
        print(f"  Remedy: {finding['remedy']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
