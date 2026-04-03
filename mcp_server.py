from __future__ import annotations

import asyncio
import json
import sys
import uuid
from contextlib import suppress
from typing import Any, AsyncIterator

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

try:
    from mcp.server.fastmcp import Context, FastMCP
except Exception:  # pragma: no cover
    Context = Any  # type: ignore[assignment]
    FastMCP = None  # type: ignore[assignment]

from config_loader import load_config
from analysis.repository_review import ensure_directory_analysis
from graphs.compliance_graph import build_compliance_graph, compile_graph
from llm.provider_factory import resolve_provider_model
from rag.ingestor import ingest, needs_ingestion
from tracing.langsmith_setup import get_run_config, resolve_run_url

_ASYNC_GRAPH = None
_ASYNC_CHECKPOINTER_CONTEXT = None


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _ensure_runtime(config: dict[str, Any]) -> None:
    try:
        if needs_ingestion(config):
            count = ingest(config)
            _stderr(f"✓ Ingested {count} chunks into ChromaDB")
    except Exception as exc:
        _stderr(f"Warning: RAG initialization failed, continuing without RAG: {exc}")


async def _get_async_graph():
    global _ASYNC_GRAPH, _ASYNC_CHECKPOINTER_CONTEXT

    if _ASYNC_GRAPH is not None:
        return _ASYNC_GRAPH

    config = load_config()
    checkpoint_config = config.get("checkpoint", {})
    backend = checkpoint_config.get("backend", "sqlite")

    if backend == "sqlite":
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        sqlite_path = checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db")
        _ASYNC_CHECKPOINTER_CONTEXT = AsyncSqliteSaver.from_conn_string(sqlite_path)
        saver = await _ASYNC_CHECKPOINTER_CONTEXT.__aenter__()
        await saver.conn.execute("PRAGMA journal_mode=WAL;")
        await saver.conn.execute("PRAGMA synchronous=NORMAL;")
        await saver.conn.commit()
        _ASYNC_GRAPH = build_compliance_graph().compile(checkpointer=saver)
    else:
        _ASYNC_GRAPH = compile_graph(config=config)

    return _ASYNC_GRAPH


async def stream_compliance_check(
    graph,
    file_path: str,
    file_content: str,
    provider: str,
    model: str,
    thread_id: str,
    line_offset: int = 0,
    reviewed_context: list[dict[str, Any]] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    active_graph = graph or await _get_async_graph()
    effective_config = load_config()
    provider, model = resolve_provider_model(provider, model, effective_config)
    initial_state = {
        "file_path": file_path,
        "file_content": file_content,
        "llm_provider": provider,
        "llm_model": model,
        "line_offset": line_offset,
        "reviewed_context": reviewed_context or [],
        "config": effective_config,
        "agentic_context": "",
        "directory_analysis_path": None,
        "workspace_root": None,
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }
    run_config = get_run_config(thread_id, file_path, provider, model)
    async for event in active_graph.astream_events(initial_state, config=run_config, version="v2"):
        yield event


def build_server():
    if FastMCP is None:
        raise RuntimeError("The `mcp` package is required to run mcp_server.py. Install requirements first.")

    if load_dotenv is not None:
        load_dotenv()

    config = load_config()
    _ensure_runtime(config)
    server = FastMCP(name="ai-ethics-compliance-agent")

    async def emit(ctx: Context | None, payload: dict[str, Any], progress: float) -> None:
        if ctx is None:
            return
        try:
            await ctx.report_progress(progress=progress, total=100, message=json.dumps(payload))
        except Exception:
            return

    async def emit_heartbeat(ctx: Context | None, file_path: str, progress_state: dict[str, float]) -> None:
        if ctx is None:
            return
        while True:
            await asyncio.sleep(15)
            await emit(
                ctx,
                {"type": "scan_progress", "data": {"message": f"Still analysing {file_path}..."}},
                progress_state["value"],
            )

    @server.tool()
    async def check_file(
        file_path: str,
        file_content: str,
        line_offset: int = 0,
        reviewed_context: list[dict[str, Any]] | None = None,
        provider: str = config.get("llm", {}).get("default_provider", "ollama_cloud"),
        model: str = config.get("llm", {}).get("default_model", "glm4:cloud"),
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        thread_id = str(uuid.uuid4())
        top_level_run_id: str | None = None
        final_output: dict[str, Any] = {}
        progress_state = {"value": 0.0}

        await emit(ctx, {"type": "scan_started", "data": {"file_path": file_path}}, progress_state["value"])
        heartbeat_task = asyncio.create_task(emit_heartbeat(ctx, file_path, progress_state))

        try:
            async for event in stream_compliance_check(
                None,
                file_path,
                file_content,
                provider,
                model,
                thread_id,
                line_offset=line_offset,
                reviewed_context=reviewed_context,
            ):
                kind = event.get("event")
                name = event.get("name")
                data = event.get("data", {}) or {}

                if kind == "on_chain_start" and name == "review_file":
                    progress_state["value"] = max(progress_state["value"], 10)
                    await emit(ctx, {"type": "scan_progress", "data": {"message": "Analysing..."}}, progress_state["value"])
                elif kind == "on_custom_event":
                    progress_state["value"] = min(progress_state["value"] + 10, 90)
                    await emit(ctx, {"type": name, "data": data}, progress_state["value"])
                elif kind == "on_chain_end" and name == "write_report":
                    final_output = data.get("output", {}) or {}
                    progress_state["value"] = 95
                elif kind == "on_chain_end" and name == "LangGraph":
                    top_level_run_id = event.get("run_id")
                elif kind == "on_chain_error":
                    raise RuntimeError(str(data))

            final_output["langsmith_run_id"] = top_level_run_id
            final_output["langsmith_run_url"] = resolve_run_url(top_level_run_id)
            await emit(
                ctx,
                {
                    "type": "scan_complete",
                    "data": {
                        "file_result": final_output.get("file_result"),
                        "final_report_md": final_output.get("final_report_md"),
                        "langsmith_run_url": final_output.get("langsmith_run_url"),
                    },
                },
                100,
            )
            return final_output
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

    @server.tool()
    async def refresh_directory_analysis(
        target_directory: str,
        force: bool = True,
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        await emit(
            ctx,
            {"type": "directory_analysis_started", "data": {"target_directory": target_directory, "force": force}},
            0,
        )
        analysis = await asyncio.to_thread(
            ensure_directory_analysis,
            target_directory,
            load_config(),
            force,
        )
        await emit(
            ctx,
            {
                "type": "directory_analysis_ready",
                "data": {
                    "path": analysis["analysis_path"],
                    "updated": analysis["updated"],
                    "file_count": analysis["file_count"],
                    "directory_count": analysis["directory_count"],
                },
            },
            100,
        )
        return analysis

    return server


if __name__ == "__main__":
    build_server().run(transport="stdio")
