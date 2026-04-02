from __future__ import annotations

import os

import streamlit as st



def render_langsmith_tab(container) -> None:
    with container.container():
        st.subheader("LangSmith")
        enabled = os.getenv("LANGSMITH_TRACING_V2", "false").lower() == "true"
        project = os.getenv("LANGSMITH_PROJECT", "ai-ethics-compliance-agent")
        st.write(f"Tracing enabled: `{enabled}`")
        st.write(f"Project: `{project}`")
        thread_id = st.session_state.get("scan_thread_id", "")
        if thread_id:
            st.write(f"Current thread id: `{thread_id}`")
        st.caption("LangGraph and LangChain spans will be emitted when LangSmith credentials are configured.")
