from __future__ import annotations

import json
import re
from typing import Any

RESULT_PATTERNS = (
    re.compile(r"<RESULT>(.*?)</RESULT>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<r>(.*?)</r>", re.DOTALL | re.IGNORECASE),
)


def extract_tagged_json(text: str) -> dict[str, Any] | None:
    candidate = text or ""
    for pattern in RESULT_PATTERNS:
        match = pattern.search(candidate)
        if not match:
            continue
        payload = match.group(1).strip()
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def slugify_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return sanitized.strip("_") or "report"


def shorten(text: str, limit: int = 240) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
