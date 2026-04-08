from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import mcp_server
from graphs.checkpointer import checkpoint_sqlite_path, ensure_sqlite_checkpoint_ready


def test_ensure_sqlite_checkpoint_ready_recovers_malformed_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "broken_checkpoints.db"
    db_path.write_bytes(b"not a sqlite database")
    (tmp_path / "broken_checkpoints.db-wal").write_bytes(b"wal")
    (tmp_path / "broken_checkpoints.db-shm").write_bytes(b"shm")

    backups = ensure_sqlite_checkpoint_ready({"checkpoint": {"sqlite_path": str(db_path)}})

    assert backups
    assert db_path.exists()
    assert any(path.name.startswith("broken_checkpoints.db.corrupt.") for path in backups)
    with sqlite3.connect(str(db_path)) as connection:
        assert connection.execute("PRAGMA quick_check;").fetchone()[0] == "ok"


def test_stream_compliance_check_recovers_from_malformed_checkpoint_once(tmp_path: Path, monkeypatch) -> None:
    sqlite_path = checkpoint_sqlite_path({"checkpoint": {"sqlite_path": str(tmp_path / "checkpoints.db")}})
    sqlite_path.write_bytes(b"broken")
    state = {"calls": 0}

    class FakeGraph:
        async def astream_events(self, initial_state, config=None, version=None):
            state["calls"] += 1
            if state["calls"] == 1:
                raise sqlite3.DatabaseError("database disk image is malformed")
            yield {"event": "on_chain_end", "name": "write_report", "data": {"output": {}}}

    async def fake_get_async_graph():
        return FakeGraph()

    async def fake_reset_async_graph():
        return None

    monkeypatch.setattr(mcp_server, "_get_async_graph", fake_get_async_graph)
    monkeypatch.setattr(mcp_server, "_reset_async_graph", fake_reset_async_graph)
    monkeypatch.setattr(mcp_server, "load_config", lambda: {"checkpoint": {"backend": "sqlite", "sqlite_path": str(sqlite_path)}})

    async def collect():
        return [
            event
            async for event in mcp_server.stream_compliance_check(
                graph=None,
                file_path=str(tmp_path / "example.py"),
                file_content="print('ok')\n",
                provider="openrouter",
                model="nvidia/nemotron-3-super-120b-a12b:free",
                thread_id="thread-recover",
            )
        ]

    events = asyncio.run(collect())

    assert state["calls"] == 2
    assert events[-1]["name"] == "write_report"
    with sqlite3.connect(str(sqlite_path)) as connection:
        assert connection.execute("PRAGMA quick_check;").fetchone()[0] == "ok"
