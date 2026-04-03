from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

_SAVER_CACHE: dict[str, Any] = {}


def get_checkpointer(config: dict[str, Any] | None = None):
    effective = config or {}
    checkpoint_config = effective.get("checkpoint", {})
    backend = os.getenv("CHECKPOINT_BACKEND", checkpoint_config.get("backend", "sqlite"))

    if backend == "postgres":
        uri_env = checkpoint_config.get("postgres_uri_env", "POSTGRES_URI")
        uri = os.getenv(uri_env)
        if not uri:
            raise EnvironmentError(f"{uri_env} must be set when CHECKPOINT_BACKEND=postgres")
        from langgraph.checkpoint.postgres import PostgresSaver

        saver_or_context = PostgresSaver.from_conn_string(uri)
        return saver_or_context.__enter__() if hasattr(saver_or_context, "__enter__") else saver_or_context

    sqlite_path = os.getenv("CHECKPOINT_DB_PATH", checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db"))
    if sqlite_path in _SAVER_CACHE:
        return _SAVER_CACHE[sqlite_path]

    from langgraph.checkpoint.sqlite import SqliteSaver

    connection = sqlite3.connect(sqlite_path, check_same_thread=False)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    saver = SqliteSaver(connection)
    _SAVER_CACHE[sqlite_path] = saver
    return saver


def list_checkpoint_thread_ids(config: dict[str, Any] | None = None) -> list[str]:
    effective = config or {}
    checkpoint_config = effective.get("checkpoint", {})
    sqlite_path = Path(os.getenv("CHECKPOINT_DB_PATH", checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db")))
    if not sqlite_path.exists():
        return []
    thread_ids: set[str] = set()
    try:
        with sqlite3.connect(sqlite_path) as connection:
            cursor = connection.execute("SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id IS NOT NULL")
            thread_ids.update(row[0] for row in cursor.fetchall() if row and row[0])
    except Exception:
        return []
    return sorted(thread_ids)
