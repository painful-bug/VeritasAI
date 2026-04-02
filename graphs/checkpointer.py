from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

_SAVER_CACHE: dict[str, Any] = {}
_CONTEXT_CACHE: dict[str, Any] = {}
_SQLITE_CONNECTIONS: dict[str, sqlite3.Connection] = {}


def get_checkpointer(config: dict[str, Any] | None = None):
    cfg = config or {}
    checkpoint_config = cfg.get("checkpoint", {})
    backend = os.getenv("CHECKPOINT_BACKEND", checkpoint_config.get("backend", "sqlite"))

    if backend == "postgres":
        uri_env = checkpoint_config.get("postgres_uri_env", "POSTGRES_URI")
        uri = os.getenv(uri_env)
        if not uri:
            raise EnvironmentError(f"{uri_env} must be set when CHECKPOINT_BACKEND=postgres")
        from langgraph.checkpoint.postgres import PostgresSaver

        if uri not in _SAVER_CACHE:
            saver_or_context = PostgresSaver.from_conn_string(uri)
            if hasattr(saver_or_context, "__enter__"):
                _CONTEXT_CACHE[uri] = saver_or_context
                _SAVER_CACHE[uri] = saver_or_context.__enter__()
            else:
                _SAVER_CACHE[uri] = saver_or_context
        return _SAVER_CACHE[uri]

    sqlite_path = os.getenv("CHECKPOINT_DB_PATH", checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db"))
    from langgraph.checkpoint.sqlite import SqliteSaver

    if sqlite_path not in _SAVER_CACHE:
        connection = sqlite3.connect(sqlite_path, check_same_thread=False)
        _SQLITE_CONNECTIONS[sqlite_path] = connection
        _SAVER_CACHE[sqlite_path] = SqliteSaver(connection)
    return _SAVER_CACHE[sqlite_path]


def list_checkpoint_thread_ids(config: dict[str, Any] | None = None) -> list[str]:
    cfg = config or {}
    checkpoint_config = cfg.get("checkpoint", {})
    sqlite_path = Path(os.getenv("CHECKPOINT_DB_PATH", checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db")))
    if not sqlite_path.exists():
        return []

    thread_ids: set[str] = set()
    try:
        with sqlite3.connect(sqlite_path) as connection:
            cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                try:
                    column_cursor = connection.execute(f"PRAGMA table_info({table})")
                    columns = [row[1] for row in column_cursor.fetchall()]
                    if "thread_id" not in columns:
                        continue
                    value_cursor = connection.execute(f"SELECT DISTINCT thread_id FROM {table} WHERE thread_id IS NOT NULL")
                    thread_ids.update(row[0] for row in value_cursor.fetchall() if row and row[0])
                except sqlite3.DatabaseError:
                    continue
    except sqlite3.DatabaseError:
        return []

    return sorted(thread_ids, reverse=True)
