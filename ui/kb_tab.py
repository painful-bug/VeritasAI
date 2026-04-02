from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from rag.ingestor import ingest, needs_ingestion
from tools.rag_tool import query_rag_tool



def render_kb_tab(container, config: dict[str, Any]) -> None:
    rag_config = config.get("rag", {})
    pdf_path = Path(rag_config.get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf"))
    with container.container():
        st.subheader("Knowledge Base")
        st.write(f"PDF: `{pdf_path}`")
        st.write(f"Vector store: `{rag_config.get('persist_dir', '.chroma_db')}`")
        if not pdf_path.exists():
            st.info("Knowledge base PDF is not present yet. Scans will still run, but RAG retrieval is disabled until the file is added.")
            return

        try:
            ingestion_needed = needs_ingestion(config)
        except Exception as exc:
            st.warning(f"Could not inspect the vector store: {exc}")
            ingestion_needed = True

        st.write("Status: needs ingestion" if ingestion_needed else "Status: ready")
        if st.button("Ingest / Rebuild KB"):
            with st.spinner("Building vector store..."):
                try:
                    count = ingest(config)
                    st.success(f"Ingested {count} chunks into the knowledge base.")
                except Exception as exc:
                    st.error(str(exc))

        query = st.text_input("Debug query", value="automated hiring decision using gender and age")
        if st.button("Run KB Query"):
            try:
                results = query_rag_tool(description=query, top_k=int(rag_config.get("top_k", 5)), config=config)
                st.json(results)
            except Exception as exc:
                st.error(str(exc))
