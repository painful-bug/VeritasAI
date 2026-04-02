#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Any

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
from graphs.compliance_graph import compile_graph
from rag.ingestor import ingest, needs_ingestion
from tools.rag_tool import query_rag_tool
from tracing.langsmith_setup import get_run_config

DEFAULT_PROBE_QUERY = "automated hiring decision using demographic attributes gender age"
DEFAULT_TARGET = REPO_ROOT / "demo_violations" / "unsafe_hiring_fixture"
DEFAULT_FOCUS_FILE = DEFAULT_TARGET / "unsafe_hiring_screen.py"
STATUS_SCORE = {"FAIL": 4, "WARN": 3, "PASS": 2, "SKIPPED": 1, "ERROR": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify RAG retrieval and run a compliance scan on the synthetic unsafe fixture.")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML. Default: config.yaml")
    parser.add_argument("--target-dir", default=str(DEFAULT_TARGET), help="Directory to scan.")
    parser.add_argument("--focus-file", default=str(DEFAULT_FOCUS_FILE), help="Primary file whose findings should be checked.")
    parser.add_argument("--provider", default=None, help="LLM provider override. Defaults to llm.default_provider from config.")
    parser.add_argument("--model", default=None, help="LLM model override. Defaults to llm.default_model from config.")
    parser.add_argument("--probe-query", default=DEFAULT_PROBE_QUERY, help="RAG query used to confirm retrieval.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of RAG hits to print.")
    parser.add_argument("--force-ingest", action="store_true", help="Rebuild the vector store before scanning.")
    return parser.parse_args()


def build_initial_state(target_directory: str, provider: str, model: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_directory": str(Path(target_directory).expanduser().resolve()),
        "config": config,
        "llm_provider": provider,
        "llm_model": model,
        "all_files": [],
        "skipped_files": [],
        "file_categories": {},
        "file_results": [],
        "progress_events": [],
        "final_report_md": None,
        "final_report_html": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }


def ensure_rag_ready(config: dict[str, Any], probe_query: str, top_k: int, force_ingest: bool) -> list[dict[str, Any]]:
    rag_config = config.get("rag", {})
    pdf_path = Path(rag_config.get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf"))

    if force_ingest or needs_ingestion(config):
        if not pdf_path.exists():
            raise FileNotFoundError(f"Knowledge base PDF not found: {pdf_path}")
        print("Refreshing vector store from the knowledge-base PDF...")
        ingest(config)

    hits = query_rag_tool(description=probe_query, top_k=top_k, config=config)
    if hits:
        return hits

    if not pdf_path.exists():
        raise RuntimeError("RAG probe returned no hits and the knowledge-base PDF is missing, so re-ingestion is not possible.")

    print("RAG probe returned no hits. Re-ingesting once to refresh the store...")
    ingest(config)
    hits = query_rag_tool(description=probe_query, top_k=top_k, config=config)
    if not hits:
        raise RuntimeError("RAG probe still returned no hits after re-ingestion.")
    return hits


def dedupe_results(state: dict[str, Any]) -> list[dict[str, Any]]:
    combined = list(state.get("_deduped_file_results") or []) + list(state.get("file_results") or [])
    best_by_file: dict[str, dict[str, Any]] = {}
    for result in combined:
        key = str(result.get("file_path", ""))
        if not key:
            continue
        current = best_by_file.get(key)
        if current is None or result_quality(result) > result_quality(current):
            best_by_file[key] = result
    return list(best_by_file.values())


def result_quality(result: dict[str, Any]) -> tuple[int, int, int, int, int]:
    validated_sources = sum(1 for source in result.get("data_sources", []) if source.get("verdict") != "PENDING")
    return (
        STATUS_SCORE.get(str(result.get("status", "ERROR")), 0),
        1 if not result.get("error") else 0,
        len(result.get("findings", [])),
        validated_sources,
        1 if result.get("report_path") else 0,
    )


def print_probe_hits(hits: list[dict[str, Any]]) -> None:
    print("RAG probe hits:")
    for index, hit in enumerate(hits, start=1):
        metadata = hit.get("metadata", {}) or {}
        excerpt = " ".join(str(hit.get("text", "")).split())[:220]
        print(
            f"{index}. chunk={metadata.get('chunk_id', 'n/a')} "
            f"page={metadata.get('page', 'n/a')} score={hit.get('score')}"
        )
        print(f"   {excerpt}")


def run_graph_scan(target_dir: Path, provider: str, model: str, config: dict[str, Any]) -> dict[str, Any]:
    graph = compile_graph(config=config)
    thread_id = str(uuid.uuid4())
    run_config = get_run_config(thread_id, str(target_dir), provider, model)
    run_config["max_concurrency"] = int(
        config.get("scan", {}).get("max_concurrency", config.get("scan", {}).get("max_parallel_agents", 4))
    )
    return graph.invoke(build_initial_state(str(target_dir), provider, model, config), config=run_config)


def find_focus_result(results: list[dict[str, Any]], focus_file: Path) -> dict[str, Any] | None:
    return next((result for result in results if Path(result["file_path"]).resolve() == focus_file), None)


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()
    config = load_config(args.config)
    provider = args.provider or config.get("llm", {}).get("default_provider", "openrouter")
    model = args.model or config.get("llm", {}).get("default_model", "")
    target_dir = Path(args.target_dir).expanduser().resolve()
    focus_file = Path(args.focus_file).expanduser().resolve()

    if not target_dir.exists():
        print(f"Target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    print(f"Target directory: {target_dir}")
    print(f"Focus file: {focus_file}")
    print(f"Provider/model: {provider}/{model}")
    print()

    hits = ensure_rag_ready(config, args.probe_query, args.top_k, args.force_ingest)
    print_probe_hits(hits)
    print()

    state = run_graph_scan(target_dir, provider, model, config)

    if state.get("scan_error"):
        print(f"Scan failed: {state['scan_error']}", file=sys.stderr)
        return 2

    results = dedupe_results(state)
    if not results:
        print("Scan produced no file results.", file=sys.stderr)
        return 3

    focus_result = find_focus_result(results, focus_file)
    if focus_result is None:
        print(f"Focus file was not included in scan results: {focus_file}", file=sys.stderr)
        return 4

    if focus_result.get("status") == "ERROR" or not focus_result.get("findings"):
        print("Primary graph run returned a degraded focus-file result. Re-running in deterministic-only mode...")
        state = run_graph_scan(target_dir, "deterministic", "deterministic", config)
        if state.get("scan_error"):
            print(f"Deterministic retry failed: {state['scan_error']}", file=sys.stderr)
            return 2
        results = dedupe_results(state)
        focus_result = find_focus_result(results, focus_file)
        if focus_result is None:
            print(f"Focus file was not included in deterministic retry results: {focus_file}", file=sys.stderr)
            return 4

    print(f"Scan status for {focus_result['file_path']}: {focus_result['status']}")
    print(f"Summary: {focus_result.get('summary') or 'No summary'}")
    print(f"Predicted output: {focus_result.get('predicted_output') or 'n/a'}")
    print()

    findings = focus_result.get("findings", [])
    if not findings:
        print("The focus file produced no findings, which is not expected for this fixture.", file=sys.stderr)
        return 5

    cited_findings = [finding for finding in findings if finding.get("rag_chunk_id") or finding.get("rag_page")]
    if not cited_findings:
        print("The scan flagged findings, but none of them included knowledge-base citations.", file=sys.stderr)
        return 6

    print("Findings:")
    for finding in findings:
        print(f"- {finding['id']} [{finding['severity']}] {finding['title']}")
        print(f"  Regulations: {', '.join(finding.get('regulations', [])) or 'None'}")
        print(f"  Explanation: {finding.get('explanation', '')}")
        print(
            f"  KB citation: chunk={finding.get('rag_chunk_id') or 'n/a'} "
            f"page={finding.get('rag_page') or 'n/a'}"
        )

    data_sources = focus_result.get("data_sources", [])
    if data_sources:
        print()
        print("Data-source review:")
        for source in data_sources:
            print(f"- {source['url_or_path']} => {source['verdict']}")
            if source.get("rag_citations"):
                citation = source["rag_citations"][0]
                print(
                    f"  KB citation: chunk={citation.get('chunk_id') or 'n/a'} "
                    f"page={citation.get('page') or 'n/a'}"
                )
            if source.get("concerns"):
                print(f"  Concern: {'; '.join(source['concerns'])}")

    output_dir = target_dir / config.get("scan", {}).get("output_dir", "compliance-analysis")
    print()
    print(f"Report directory: {output_dir}")
    print(f"Final markdown report: {output_dir / 'final_compliance_report.md'}")
    print(f"Final HTML report: {output_dir / 'final_compliance_report.html'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
