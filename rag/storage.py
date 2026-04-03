from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.shared_system_client import SharedSystemClient


def _validate_client(client: Any) -> None:
    try:
        heartbeat = getattr(client, "heartbeat", None)
        if callable(heartbeat):
            heartbeat()
        else:
            client.list_collections()
    except Exception:
        client.list_collections()


def create_persistent_client(persist_dir: str):
    client = chromadb.PersistentClient(path=persist_dir)
    _validate_client(client)
    return client


def archive_persist_dir(persist_dir: str) -> Path | None:
    source = Path(persist_dir)
    if not source.exists():
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archived = source.with_name(f"{source.name}.corrupt-{timestamp}")
    shutil.move(str(source), str(archived))
    return archived


def create_persistent_client_with_recovery(persist_dir: str) -> tuple[Any, Path | None]:
    try:
        return create_persistent_client(persist_dir), None
    except Exception:
        SharedSystemClient.clear_system_cache()
        archived = archive_persist_dir(persist_dir)
        return create_persistent_client(persist_dir), archived
