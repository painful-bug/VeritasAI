from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

try:
    from langchain.tools import tool
except Exception:  # pragma: no cover
    from utils.compat import tool

from filelock import FileLock, Timeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

try:
    import chardet
except Exception:  # pragma: no cover
    chardet = None

from utils.compat import traceable


def _safe_path(path: str, allowed_root: Optional[str] = None) -> Path:
    resolved = Path(path).expanduser().resolve()
    if allowed_root:
        root = Path(allowed_root).expanduser().resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"Path traversal detected: {path} escapes {allowed_root}")
    return resolved


def safe_resolve_path(path: str | Path, allowed_root: str | Path | None = None) -> Path:
    return _safe_path(str(path), str(allowed_root) if allowed_root else None)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.2, max=2))
def safe_mkdir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _detect_encoding(header: bytes) -> str:
    if chardet is not None:
        try:
            detected = chardet.detect(header)
        except Exception:
            detected = None
        if detected and detected.get("encoding"):
            return str(detected["encoding"])
    return "utf-8"


@traceable(name="read_file", tags=["filesystem"])
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=0.5, max=4),
    retry=retry_if_exception_type(OSError),
)
def read_text_file(
    path: str | Path,
    start_line: int = 1,
    end_line: int = -1,
    allowed_root: str | Path | None = None,
) -> str:
    resolved = safe_resolve_path(path, allowed_root)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Path is a directory: {path}")

    with resolved.open("rb") as handle:
        header = handle.read(8192)
        remainder = handle.read()

    if b"\x00" in header:
        return f"<binary file: {resolved}>"

    text = (header + remainder).decode(_detect_encoding(header), errors="replace")
    lines = text.splitlines(keepends=True)
    lower = max(0, start_line - 1)
    upper = len(lines) if end_line == -1 else max(lower, end_line)
    return "".join(lines[lower:upper])


@tool
def read_file_tool(path: str, start_line: int = 1, end_line: int = -1) -> str:
    """Read a file with optional 1-based inclusive line bounds."""
    return read_text_file(path, start_line=start_line, end_line=end_line)


@traceable(name="write_file", tags=["filesystem"])
def write_text_file(path: str | Path, content: str, lock_timeout: int = 30) -> str:
    resolved = safe_resolve_path(path)
    safe_mkdir(resolved.parent)
    lock_path = f"{resolved}.lock"
    try:
        with FileLock(lock_path, timeout=lock_timeout):
            fd, tmp_path = tempfile.mkstemp(dir=str(resolved.parent), prefix=f".{resolved.name}.tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(content)
                shutil.move(tmp_path, resolved)
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
    except Timeout as exc:
        raise RuntimeError(f"Could not acquire write lock for {path} within {lock_timeout}s") from exc
    return str(resolved)


@tool
def write_file_tool(path: str, content: str) -> str:
    """Atomically write UTF-8 text content to a file."""
    written = write_text_file(path, content)
    return f"OK: wrote {Path(written).stat().st_size} bytes to {written}"
