from __future__ import annotations

import os
from typing import Any

from utils.compat import tool, traceable

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except Exception:  # pragma: no cover - optional dependency at dev time
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalized_tavily_api_key() -> str | None:
    raw = os.getenv("TAVILY_API_KEY", "").strip()
    if not raw:
        return None
    if raw.startswith("TAVILY_API_KEY="):
        raw = raw.split("=", 1)[1].strip()
    return raw or None


@tool
@traceable(name="web_search", tags=["web"])
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def web_search_tool(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    """Search the web for provenance or policy context when a stable provider is configured."""
    if not query.strip():
        return []

    api_key = _normalized_tavily_api_key()
    if api_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            response = client.search(query, max_results=max_results)
            return list(response.get("results", []))
        except Exception:
            pass

    if not _truthy(os.getenv("ENABLE_DDGS_FALLBACK")):
        return []

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []
