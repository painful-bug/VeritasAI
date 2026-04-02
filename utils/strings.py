from __future__ import annotations

import json
import re
from typing import Any

RESULT_PATTERN = re.compile(r"<RESULT>(.*?)</RESULT>", re.DOTALL | re.IGNORECASE)


def extract_tagged_json(text: str) -> dict[str, Any] | None:
    match = RESULT_PATTERN.search(text or "")
    if not match:
        return None
    payload = match.group(1).strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def slugify_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return sanitized.strip("_") or "report"


def shorten(text: str, limit: int = 240) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
