from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import streamlit as st

from llm.provider_factory import get_available_models, provider_requires_api_key, test_connection


def _secret_or_env_is_configured(key: str) -> bool:
    try:
        secret_value = st.secrets.get(key, None)
    except Exception:
        secret_value = None
    return bool(secret_value or os.getenv(key))



def render_sidebar(config: dict[str, Any], available_threads: list[str]) -> dict[str, Any]:
    llm_config = config.get("llm", {})
    provider_options = list(llm_config.get("providers", {}).keys())
    default_provider = llm_config.get("default_provider", provider_options[0] if provider_options else "openrouter")
    default_model = llm_config.get("default_model", "")

    st.sidebar.title("AI Ethics Compliance Agent")
    target_directory = st.sidebar.text_input("Target Directory", value=st.session_state.get("target_directory", str(Path.cwd())))
    provider = st.sidebar.selectbox(
        "LLM Provider",
        options=provider_options,
        index=provider_options.index(default_provider) if default_provider in provider_options else 0,
    )
    model_options = get_available_models(config, provider) or [default_model]
    model = st.sidebar.selectbox(
        "Model",
        options=model_options,
        index=model_options.index(default_model) if default_model in model_options else 0,
    )
    use_llm_enrichment = st.sidebar.checkbox(
        "Use LLM Enrichment",
        value=st.session_state.get("use_llm_enrichment", True),
        help="When disabled, scans run in deterministic-only mode for maximum stability and speed.",
    )

    required_key = provider_requires_api_key(provider)
    if not use_llm_enrichment:
        st.sidebar.caption("Runtime mode: deterministic-only scan")
    elif required_key:
        value = "configured" if _secret_or_env_is_configured(required_key) else "missing"
        st.sidebar.caption(f"{required_key}: {value}")
    else:
        st.sidebar.caption("No API key required for this provider.")

    test_clicked = st.sidebar.button("Test Connection")
    test_result: tuple[bool, str] | None = None
    if test_clicked:
        with st.sidebar:
            with st.spinner("Testing provider connection..."):
                test_result = test_connection(provider, model, config)
        if test_result[0]:
            st.sidebar.success(test_result[1])
        else:
            st.sidebar.warning(test_result[1])

    if available_threads:
        selected_thread = st.sidebar.selectbox("Resume Thread", options=available_threads)
    else:
        selected_thread = ""
        st.sidebar.caption("No checkpoint threads found yet.")

    start_scan = st.sidebar.button("Start Scan", type="primary")
    resume_scan = st.sidebar.button("Resume Scan", disabled=not bool(selected_thread))

    st.sidebar.divider()
    st.sidebar.markdown("**Status**")
    st.sidebar.caption(f"Scan: {st.session_state.get('scan_status', 'IDLE')}")
    st.sidebar.caption(f"Checkpoint DB: {config.get('checkpoint', {}).get('sqlite_path', '.langgraph_checkpoints.db')}")

    st.session_state["target_directory"] = target_directory
    st.session_state["use_llm_enrichment"] = use_llm_enrichment
    return {
        "target_directory": target_directory,
        "provider": provider,
        "model": model,
        "use_llm_enrichment": use_llm_enrichment,
        "start_scan": start_scan,
        "resume_scan": resume_scan,
        "selected_thread": selected_thread,
        "test_result": test_result,
    }
