from __future__ import annotations

from typing import Any

try:
    from langchain.tools import tool
except Exception:  # pragma: no cover
    from utils.compat import tool

from config_loader import load_config
from rag.retriever import Retriever
from utils.compat import traceable


@tool
@traceable(name="query_rag", tags=["rag"])
def query_rag_tool(description: str, top_k: int = 3, min_trust: float | None = None) -> list[dict[str, Any]]:
    """Query the local AI ethics knowledge base."""
    retriever = Retriever.get_instance(load_config())
    return retriever.query(description, top_k=top_k, min_trust=min_trust, expand_query=True)
