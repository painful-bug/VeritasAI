from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def progress_event(event_type: str, file_path: str = "", message: str = "", **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_type": event_type,
        "file_path": file_path,
        "message": message,
        "timestamp": now_iso(),
    }
    payload.update(extra)
    return payload
