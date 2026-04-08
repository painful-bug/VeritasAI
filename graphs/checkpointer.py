from __future__ import annotations

import os
import sqlite3
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SAVER_CACHE: dict[str, Any] = {}


def checkpoint_backend(config: dict[str, Any] | None = None) -> str:
    effective = config or {}
    checkpoint_config = effective.get("checkpoint", {})
    return str(os.getenv("CHECKPOINT_BACKEND", checkpoint_config.get("backend", "sqlite")) or "sqlite").strip()


def checkpoint_sqlite_path(config: dict[str, Any] | None = None) -> Path:
    effective = config or {}
    checkpoint_config = effective.get("checkpoint", {})
    raw_path = os.getenv("CHECKPOINT_DB_PATH", checkpoint_config.get("sqlite_path", ".langgraph_checkpoints.db"))
    return Path(str(raw_path)).expanduser().resolve()


def is_sqlite_malformed_error(exc: Exception) -> bool:
    if not isinstance(exc, sqlite3.DatabaseError):
        return False
    message = str(exc).lower()
    return "database disk image is malformed" in message or "malformed" in message


def _checkpoint_sidecar_paths(sqlite_path: Path) -> list[Path]:
    return [sqlite_path, Path(f"{sqlite_path}-wal"), Path(f"{sqlite_path}-shm")]


def _checkpoint_health(sqlite_path: Path) -> tuple[bool, str]:
    if not sqlite_path.exists():
        return True, "missing"
    try:
        with sqlite3.connect(str(sqlite_path)) as connection:
            rows = [str(row[0]) for row in connection.execute("PRAGMA quick_check;").fetchall() if row]
    except Exception as exc:
        return False, str(exc)
    if rows == ["ok"]:
        return True, "ok"
    return False, "; ".join(rows[:20]) or "PRAGMA quick_check failed"


def _close_cached_saver(sqlite_path: Path) -> None:
    saver = _SAVER_CACHE.pop(str(sqlite_path), None)
    connection = getattr(saver, "conn", None)
    if connection is not None:
        with suppress(Exception):
            connection.close()


def recover_sqlite_checkpoint(
    sqlite_path: str | Path,
    *,
    reason: str = "checkpoint database is malformed",
) -> list[Path]:
    path = Path(sqlite_path).expanduser().resolve()
    _close_cached_saver(path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups: list[Path] = []
    for candidate in _checkpoint_sidecar_paths(path):
        if not candidate.exists():
            continue
        backup = candidate.with_name(f"{candidate.name}.corrupt.{timestamp}")
        candidate.replace(backup)
        backups.append(backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as connection:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA synchronous=NORMAL;")
    return backups


def ensure_sqlite_checkpoint_ready(config: dict[str, Any] | None = None) -> list[Path]:
    sqlite_path = checkpoint_sqlite_path(config)
    healthy, detail = _checkpoint_health(sqlite_path)
    if healthy:
        return []
    return recover_sqlite_checkpoint(sqlite_path, reason=detail)


def get_checkpointer(config: dict[str, Any] | None = None):
    effective = config or {}
    checkpoint_config = effective.get("checkpoint", {})
    backend = checkpoint_backend(effective)

    if backend == "postgres":
        uri_env = checkpoint_config.get("postgres_uri_env", "POSTGRES_URI")
        uri = os.getenv(uri_env)
        if not uri:
            raise EnvironmentError(f"{uri_env} must be set when CHECKPOINT_BACKEND=postgres")
        from langgraph.checkpoint.postgres import PostgresSaver

        saver_or_context = PostgresSaver.from_conn_string(uri)
        return saver_or_context.__enter__() if hasattr(saver_or_context, "__enter__") else saver_or_context

    sqlite_path = checkpoint_sqlite_path(effective)
    if str(sqlite_path) in _SAVER_CACHE:
        return _SAVER_CACHE[str(sqlite_path)]

    ensure_sqlite_checkpoint_ready(effective)

    from langgraph.checkpoint.sqlite import SqliteSaver

    connection = sqlite3.connect(str(sqlite_path), check_same_thread=False)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    saver = SqliteSaver(connection)
    _SAVER_CACHE[str(sqlite_path)] = saver
    return saver


def list_checkpoint_thread_ids(config: dict[str, Any] | None = None) -> list[str]:
    sqlite_path = checkpoint_sqlite_path(config)
    if not sqlite_path.exists():
        return []
    thread_ids: set[str] = set()
    try:
        with sqlite3.connect(str(sqlite_path)) as connection:
            cursor = connection.execute("SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id IS NOT NULL")
            thread_ids.update(row[0] for row in cursor.fetchall() if row and row[0])
    except Exception:
        return []
    return sorted(thread_ids)
