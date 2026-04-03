from __future__ import annotations

import json
import importlib
import os
from dataclasses import dataclass
from typing import Any, Callable

from rag.retriever import Retriever
from utils.strings import extract_tagged_json

WebSearchFn = Callable[[str, int], list[dict[str, Any]]]


def _compact_rag_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for hit in hits:
        metadata = hit.get("metadata", {}) or {}
        compact.append(
            {
                "chunk_id": str(metadata.get("chunk_id") or ""),
                "page": int(metadata.get("page", 0) or 0),
                "jurisdiction": str(metadata.get("jurisdiction") or "Global"),
                "confidence": float(hit.get("confidence", 0.0) or 0.0),
                "trust_score": float(hit.get("trust_score", 0.0) or 0.0),
                "text": str(hit.get("text", ""))[:2000],
            }
        )
    return compact


def _compact_web_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for hit in hits:
        compact.append(
            {
                "source": str(hit.get("source") or "web"),
                "title": str(hit.get("title") or hit.get("source") or "web result"),
                "url": str(hit.get("url") or ""),
                "content": str(hit.get("content") or hit.get("snippet") or hit.get("body") or "")[:2000],
            }
        )
    return compact


def _payload_from_text(text: str) -> dict[str, Any] | None:
    payload = extract_tagged_json(text)
    if payload is not None:
        return payload
    candidate = (text or "").strip()
    if not candidate:
        return None
    try:
        parsed = json.loads(candidate)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _needs_web(payload: dict[str, Any], relevancy_force_threshold: float) -> bool:
    explicit = payload.get("Needs Web Search")
    if isinstance(explicit, bool):
        return explicit
    relevancy = _to_float(payload.get("Relevancy"), 0.0)
    return relevancy <= relevancy_force_threshold


def _build_system_prompt() -> str:
    return (
        "You are an AI ethics compliance reviewer. "
        "You must first use retriever_tool to fetch local regulatory context. "
        "Then review the file and output ONLY JSON inside <r>...</r>. "
        "Include exactly these keys: Relevancy, Faithfulness, Context Quality, Needs Web Search, "
        "Explanation, Answer, summary, status, findings. "
        "findings must be a list with items containing severity, start_line, end_line, regulation_name, "
        "jurisdiction, explanation, remedy, rag_chunk_id, rag_page. "
        "All scores must be floats between 0 and 1."
    )


@dataclass
class _Deps:
    question: str
    context: str
    top_k: int


def _can_use_pydantic_runtime(provider: str) -> bool:
    if provider != "groq":
        return False
    return bool(os.getenv("GROQ_API_KEY"))


# Returns payload + retrieval and web traces when PydanticAI route is available.
def run_pydantic_agentic_review(
    *,
    provider: str,
    model: str,
    question: str,
    context: str,
    retriever: Retriever,
    web_search_fn: WebSearchFn | None,
    top_k: int,
    max_retries: int,
    max_web_results: int,
    force_web_threshold: float,
) -> dict[str, Any] | None:
    if not _can_use_pydantic_runtime(provider):
        return None

    try:
        pydantic_ai_module = importlib.import_module("pydantic_ai")
        groq_module = importlib.import_module("pydantic_ai.models.groq")
        Agent = getattr(pydantic_ai_module, "Agent")
        RunContext = getattr(pydantic_ai_module, "RunContext")
        GroqModel = getattr(groq_module, "GroqModel")
    except Exception:
        return None

    rag_trace: list[dict[str, Any]] = []
    web_trace: list[dict[str, Any]] = []

    groq_model = GroqModel(model or "llama-3.3-70b-versatile")
    agent = Agent(
        groq_model,
        deps_type=_Deps,
        retries=max_retries,
        result_type=str,
        system_prompt=_build_system_prompt(),
    )

    @agent.tool
    async def retriever_tool(ctx: Any, question: str) -> list[dict[str, Any]]:
        hits = retriever.query_for_compliance(question, top_k=ctx.deps.top_k)
        compact = _compact_rag_hits(hits)
        rag_trace.extend(compact)
        return compact

    @agent.tool_plain
    async def websearch_tool(question: str) -> list[dict[str, Any]]:
        if web_search_fn is None:
            return []
        hits = web_search_fn(question, max_web_results)
        compact = _compact_web_hits(hits)
        web_trace.extend(compact)
        return compact

    try:
        run = agent.run_sync(
            (
                f"Question: {question}\n\n"
                f"Context:\n{context}\n\n"
                "If context is insufficient, set Needs Web Search to true."
            ),
            deps=_Deps(question=question, context=context, top_k=top_k),
        )
    except Exception:
        return None

    raw = run.data if hasattr(run, "data") else str(run)
    payload = _payload_from_text(raw if isinstance(raw, str) else str(raw))
    if payload is None:
        return None

    if _needs_web(payload, relevancy_force_threshold=force_web_threshold):
        if web_search_fn is not None and not web_trace:
            web_trace.extend(_compact_web_hits(web_search_fn(question, max_web_results)))

        if web_trace:
            augmented_context = (
                f"{context}\n\n"
                f"Web context:\n{json.dumps(web_trace, ensure_ascii=True)}\n\n"
                "Re-evaluate and return final JSON in <r>...</r>."
            )
            try:
                rerun = agent.run_sync(
                    f"Question: {question}\n\nContext:\n{augmented_context}",
                    deps=_Deps(question=question, context=augmented_context, top_k=top_k),
                )
                reraw = rerun.data if hasattr(rerun, "data") else str(rerun)
                repayload = _payload_from_text(reraw if isinstance(reraw, str) else str(reraw))
                if repayload is not None:
                    payload = repayload
            except Exception:
                # Keep first-pass payload if rerun fails.
                pass

    return {
        "payload": payload,
        "rag_trace": rag_trace,
        "web_trace": web_trace,
        "runtime": "pydantic_ai",
    }
