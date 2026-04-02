from __future__ import annotations

import streamlit as st



def render_report_tab(container) -> None:
    with container.container():
        st.subheader("Report Viewer")
        markdown = st.session_state.get("final_report_md", "")
        html = st.session_state.get("final_report_html", "")
        if not markdown and not html:
            st.info("No report is available yet.")
            return

        view = st.radio("View", options=["Markdown", "HTML"], horizontal=True)
        if view == "Markdown":
            st.markdown(markdown)
        else:
            st.components.v1.html(html, height=720, scrolling=True)

        if markdown:
            st.download_button("Download Markdown", markdown, file_name="final_compliance_report.md")
        if html:
            st.download_button("Download HTML", html, file_name="final_compliance_report.html")
