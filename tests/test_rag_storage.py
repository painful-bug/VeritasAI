from __future__ import annotations

from pathlib import Path

import rag.ingestor as ingestor
import rag.storage as storage


def test_create_persistent_client_with_recovery_archives_and_retries(monkeypatch, tmp_path: Path) -> None:
    persist_dir = tmp_path / ".chroma_db"
    persist_dir.mkdir()
    archived_dir = tmp_path / ".chroma_db.corrupt-20260402T000000Z"
    client = object()
    calls: list[str] = []

    def fake_create(path: str):
        calls.append(path)
        if len(calls) == 1:
            raise RuntimeError("broken bindings")
        return client

    monkeypatch.setattr(storage, "create_persistent_client", fake_create)
    monkeypatch.setattr(storage, "archive_persist_dir", lambda path: archived_dir)

    recovered_client, archived = storage.create_persistent_client_with_recovery(str(persist_dir))

    assert recovered_client is client
    assert archived == archived_dir
    assert calls == [str(persist_dir), str(persist_dir)]


def test_needs_ingestion_returns_true_after_recovery(monkeypatch, tmp_path: Path) -> None:
    class DummyClient:
        def get_collection(self, name: str):
            raise RuntimeError(f"missing collection: {name}")

    archived_dir = tmp_path / ".chroma_db.corrupt-20260402T000000Z"
    monkeypatch.setattr(
        ingestor,
        "create_persistent_client_with_recovery",
        lambda path: (DummyClient(), archived_dir),
    )

    assert (
        ingestor.needs_ingestion(
            {
                "rag": {
                    "chroma_persist_dir": str(tmp_path / ".chroma_db"),
                    "collection_name": "ai_ethics_kb",
                }
            }
        )
        is True
    )


def test_needs_ingestion_returns_false_for_populated_collection(monkeypatch, tmp_path: Path) -> None:
    class DummyCollection:
        def count(self) -> int:
            return 100

    class DummyClient:
        def get_collection(self, name: str) -> DummyCollection:
            return DummyCollection()

    monkeypatch.setattr(
        ingestor,
        "create_persistent_client_with_recovery",
        lambda path: (DummyClient(), None),
    )

    assert (
        ingestor.needs_ingestion(
            {
                "rag": {
                    "chroma_persist_dir": str(tmp_path / ".chroma_db"),
                    "collection_name": "ai_ethics_kb",
                }
            }
        )
        is False
    )
