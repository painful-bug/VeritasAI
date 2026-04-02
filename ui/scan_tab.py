from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st



def ensure_scan_state() -> None:
    st.session_state.setdefault("scan_rows", {})
    st.session_state.setdefault("log_lines", [])
    st.session_state.setdefault("scan_status", "IDLE")
    st.session_state.setdefault("final_report_md", "")
    st.session_state.setdefault("final_report_html", "")
    st.session_state.setdefault("scan_thread_id", "")
    st.session_state.setdefault("progress_events", [])



def reset_scan_state() -> None:
    st.session_state["scan_rows"] = {}
    st.session_state["log_lines"] = []
    st.session_state["progress_events"] = []
    st.session_state["final_report_md"] = ""
    st.session_state["final_report_html"] = ""



def consume_node_output(output: dict[str, Any]) -> None:
    if not isinstance(output, dict):
        return

    for event in output.get("progress_events", []):
        st.session_state["progress_events"].append(event)
        label = event.get("file_path") or event.get("event_type")
        st.session_state["log_lines"].append(f"[{event.get('timestamp', '')}] {label}: {event.get('message', '')}")

    for result in output.get("file_results", []):
        st.session_state["scan_rows"][result["file_path"]] = {
            "status": result["status"],
            "type": result["file_type"],
            "findings": len(result.get("findings", [])),
        }

    if output.get("final_report_md"):
        st.session_state["final_report_md"] = output["final_report_md"]
    if output.get("final_report_html"):
        st.session_state["final_report_html"] = output["final_report_html"]



def consume_graph_event(event: dict[str, Any]) -> None:
    kind = event.get("event")
    name = event.get("name", "")
    data = event.get("data", {})

    if kind == "on_chain_start" and name == "review_file":
        current_file = data.get("input", {}).get("_current_file") if isinstance(data.get("input"), dict) else ""
        if current_file:
            st.session_state["scan_rows"][current_file] = {"status": "SCANNING", "type": "", "findings": 0}
    elif kind == "on_chain_end":
        output = data.get("output", {}) if isinstance(data, dict) else {}
        consume_node_output(output)
    elif kind == "on_tool_start":
        st.session_state["log_lines"].append(f"Tool started: {name}")
    elif kind == "on_tool_end":
        st.session_state["log_lines"].append(f"Tool completed: {name}")
    elif kind == "on_chain_error":
        st.session_state["scan_status"] = "ERROR"
        st.session_state["log_lines"].append(f"Chain error in {name}: {data}")


def consume_stream_chunk(chunk: Any) -> None:
    if isinstance(chunk, tuple) and len(chunk) == 3:
        _, mode, payload = chunk
        if mode == "tasks":
            _consume_task_event(payload)
            return
        if mode != "updates":
            return
    elif isinstance(chunk, tuple) and len(chunk) == 2:
        _, payload = chunk
    else:
        payload = chunk

    if not isinstance(payload, dict):
        return

    for node_name, output in payload.items():
        if node_name == "fan_out_files" and isinstance(output, dict):
            for file_path in output.get("all_files", []):
                st.session_state["scan_rows"].setdefault(
                    file_path,
                    {"status": "QUEUED", "type": output.get("file_categories", {}).get(file_path, ""), "findings": 0},
                )
        consume_node_output(output)


def _consume_task_event(event: dict[str, Any]) -> None:
    if not isinstance(event, dict):
        return

    name = str(event.get("name", ""))
    if name == "review_file":
        task_input = event.get("input", {}) if isinstance(event.get("input"), dict) else {}
        file_path = str(task_input.get("_current_file", ""))
        if file_path:
            st.session_state["scan_rows"][file_path] = {
                "status": "SCANNING",
                "type": str(task_input.get("_current_category", "")),
                "findings": st.session_state["scan_rows"].get(file_path, {}).get("findings", 0),
            }
            st.session_state["log_lines"].append(f"Started review: {file_path}")

    if event.get("error"):
        task_input = event.get("input", {}) if isinstance(event.get("input"), dict) else {}
        file_path = str(task_input.get("_current_file", ""))
        if file_path:
            st.session_state["scan_rows"][file_path] = {
                "status": "ERROR",
                "type": str(task_input.get("_current_category", "")),
                "findings": 0,
            }
        st.session_state["log_lines"].append(f"Task error in {name}: {event.get('error')}")



def render_scan_tab(container) -> None:
    rows = st.session_state.get("scan_rows", {})
    counts = Counter(row["status"] for row in rows.values())
    scanned = len(rows)
    complete = counts.get("PASS", 0) + counts.get("WARN", 0) + counts.get("FAIL", 0) + counts.get("ERROR", 0) + counts.get("SKIPPED", 0)
    progress = 0.0 if scanned == 0 else complete / max(scanned, 1)

    with container.container():
        st.subheader("Live Scan")
        st.progress(progress, text=f"{complete}/{max(scanned, 1)} files completed")
        st.caption(
            f"PASS={counts.get('PASS', 0)} WARN={counts.get('WARN', 0)} FAIL={counts.get('FAIL', 0)} ERROR={counts.get('ERROR', 0)} SKIPPED={counts.get('SKIPPED', 0)}"
        )
        if rows:
            table_rows = [
                {"file": path, "status": row["status"], "type": row["type"], "findings": row["findings"]}
                for path, row in sorted(rows.items())
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No files have been scanned yet.")

        st.subheader("Live Log")
        logs = st.session_state.get("log_lines", [])[-150:]
        st.code("\n".join(logs) if logs else "Waiting for scan events...", language="text")
