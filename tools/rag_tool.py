from __future__ import annotations

from typing import Any

from config_loader import load_config
from rag.retriever import Retriever
from utils.compat import tool, traceable


@tool
@traceable(name="query_rag", tags=["rag"])
def query_rag_tool(description: str, top_k: int = 5, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Query the local knowledge-base vector store for regulation-relevant passages."""
    effective_config = config or load_config()
    retriever = Retriever.get_instance(effective_config)
    return retriever.query(description, top_k=top_k)
