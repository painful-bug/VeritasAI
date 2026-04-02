from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from config_loader import load_config
from graphs.checkpointer import list_checkpoint_thread_ids
from tracing.langsmith_setup import get_run_config
from ui.kb_tab import render_kb_tab
from ui.langsmith_tab import render_langsmith_tab
from ui.report_tab import render_report_tab
from ui.scan_tab import consume_stream_chunk, ensure_scan_state, render_scan_tab, reset_scan_state
from ui.sidebar import render_sidebar

load_dotenv()

st.set_page_config(page_title="AI Ethics Compliance Agent", layout="wide")
ensure_scan_state()
CONFIG = load_config()


def build_initial_state(target_directory: str, provider: str, model: str) -> dict[str, Any]:
    return {
        "target_directory": str(Path(target_directory).expanduser().resolve()),
        "config": CONFIG,
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


def effective_runtime_model(provider: str, model: str, use_llm_enrichment: bool) -> tuple[str, str]:
    if use_llm_enrichment:
        return provider, model
    return "deterministic", "deterministic"


def run_scan(target_directory: str, provider: str, model: str, thread_id: str, initial_state: dict[str, Any] | None, live_container) -> None:
    st.session_state["scan_status"] = "RUNNING"
    st.session_state["scan_thread_id"] = thread_id

    try:
        from graphs.compliance_graph import compile_graph
    except Exception as exc:
        st.session_state["scan_status"] = "ERROR"
        st.error(f"LangGraph runtime is unavailable: {exc}")
        return

    run_config = get_run_config(thread_id, target_directory, provider, model)
    run_config["max_concurrency"] = int(CONFIG.get("scan", {}).get("max_concurrency", CONFIG.get("scan", {}).get("max_parallel_agents", 4)))

    try:
        graph = compile_graph(config=CONFIG)
        for chunk in graph.stream(initial_state, config=run_config, stream_mode=["tasks", "updates"], subgraphs=True):
            consume_stream_chunk(chunk)
            render_scan_tab(live_container)
        st.session_state["scan_status"] = "COMPLETE"
    except Exception as exc:
        st.session_state["scan_status"] = "ERROR"
        message = f"Scan failed: {exc}"
        if message not in st.session_state["log_lines"]:
            st.session_state["log_lines"].append(message)
        render_scan_tab(live_container)
        st.error(str(exc))



def main() -> None:
    available_threads = list_checkpoint_thread_ids(CONFIG)
    controls = render_sidebar(CONFIG, available_threads)

    tab_scan, tab_report, tab_kb, tab_langsmith = st.tabs(["Live Scan", "Report", "Knowledge Base", "LangSmith"])
    scan_placeholder = tab_scan.empty()
    report_placeholder = tab_report.empty()
    kb_placeholder = tab_kb.empty()
    langsmith_placeholder = tab_langsmith.empty()

    render_scan_tab(scan_placeholder)
    render_report_tab(report_placeholder)
    render_kb_tab(kb_placeholder, CONFIG)
    render_langsmith_tab(langsmith_placeholder)

    if controls["start_scan"]:
        reset_scan_state()
        runtime_provider, runtime_model = effective_runtime_model(
            controls["provider"],
            controls["model"],
            controls["use_llm_enrichment"],
        )
        initial_state = build_initial_state(controls["target_directory"], runtime_provider, runtime_model)
        run_scan(
            target_directory=controls["target_directory"],
            provider=runtime_provider,
            model=runtime_model,
            thread_id=str(uuid.uuid4()),
            initial_state=initial_state,
            live_container=scan_placeholder,
        )
        render_report_tab(report_placeholder)
        render_langsmith_tab(langsmith_placeholder)

    if controls["resume_scan"] and controls["selected_thread"]:
        reset_scan_state()
        runtime_provider, runtime_model = effective_runtime_model(
            controls["provider"],
            controls["model"],
            controls["use_llm_enrichment"],
        )
        run_scan(
            target_directory=controls["target_directory"],
            provider=runtime_provider,
            model=runtime_model,
            thread_id=controls["selected_thread"],
            initial_state=None,
            live_container=scan_placeholder,
        )
        render_report_tab(report_placeholder)
        render_langsmith_tab(langsmith_placeholder)


if __name__ == "__main__":
    main()
