from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from utils.compat import get_tool_exception_type, tool, traceable

try:
    import chardet  # type: ignore
except Exception:  # pragma: no cover - optional dependency at dev time
    chardet = None

try:
    from filelock import FileLock, Timeout  # type: ignore
except Exception:  # pragma: no cover - optional dependency at dev time
    FileLock = None
    Timeout = RuntimeError

try:
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
except Exception:  # pragma: no cover - optional dependency at dev time
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def stop_after_attempt(*args, **kwargs):
        return None

    def wait_exponential(*args, **kwargs):
        return None

    def retry_if_exception_type(*args, **kwargs):
        return None


ToolException = get_tool_exception_type()


SAFE_BANNED_PATTERNS = (
    "rm -rf /",
    "> /dev/sda",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
)



def safe_resolve_path(path: str | Path, allowed_root: str | Path | None = None) -> Path:
    resolved = Path(path).expanduser().resolve()
    if allowed_root is not None:
        root = Path(allowed_root).expanduser().resolve()
        if root != resolved and root not in resolved.parents:
            raise ValueError(f"Path traversal detected: {resolved} is outside {root}")
    return resolved


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(OSError),
)
def safe_mkdir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


@traceable(name="list_directory_robust", tags=["filesystem"])
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(OSError),
)
def list_directory_robust(
    path: str | Path,
    recursive: bool = True,
    excluded_dirs: Iterable[str] | None = None,
) -> list[dict[str, object]]:
    root = safe_resolve_path(path)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    excluded = set(excluded_dirs or [])
    results: list[dict[str, object]] = []
    iterator = root.rglob("*") if recursive else root.glob("*")
    for candidate in iterator:
        try:
            if any(part in excluded for part in candidate.parts):
                continue
            if candidate.is_symlink():
                real = candidate.resolve()
                if root != real and root not in real.parents:
                    continue
            if candidate.is_file():
                stat = candidate.stat()
                results.append(
                    {
                        "path": str(candidate),
                        "size_bytes": int(stat.st_size),
                        "mtime": float(stat.st_mtime),
                        "is_symlink": bool(candidate.is_symlink()),
                    }
                )
        except (OSError, PermissionError):
            continue
    return results



def _detect_encoding(header: bytes) -> str:
    if chardet is not None:
        detected = chardet.detect(header)
        if detected and detected.get("encoding"):
            return str(detected["encoding"])
    return "utf-8"


@traceable(name="read_file_text", tags=["filesystem"])
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
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
        raise FileNotFoundError(f"File not found: {resolved}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Path is a directory: {resolved}")

    with resolved.open("rb") as handle:
        header = handle.read(8192)
        remainder = handle.read()
    if b"\x00" in header:
        return f"<binary file: {resolved.name}>"

    encoding = _detect_encoding(header)
    raw = header + remainder
    text = raw.decode(encoding, errors="replace")
    lines = text.splitlines(keepends=True)
    lower = max(1, start_line) - 1
    upper = len(lines) if end_line == -1 else max(lower, end_line)
    return "".join(lines[lower:upper])


@tool
@traceable(name="read_file", tags=["filesystem"])
def read_file_tool(path: str, start_line: int = 1, end_line: int = -1) -> str:
    """Read a text file, optionally restricted to a 1-based inclusive line range."""
    return read_text_file(path, start_line=start_line, end_line=end_line)


@traceable(name="write_file_text", tags=["filesystem"])
def write_text_file(path: str | Path, content: str, lock_timeout: int = 30) -> str:
    resolved = safe_resolve_path(path)
    safe_mkdir(resolved.parent)

    if FileLock is None:
        resolved.write_text(content, encoding="utf-8")
        return str(resolved)

    lock = FileLock(str(resolved) + ".lock", timeout=lock_timeout)
    with lock:
        fd, tmp_path = tempfile.mkstemp(prefix=f".{resolved.name}.", dir=str(resolved.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            shutil.move(tmp_path, resolved)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    return str(resolved)


@tool
@traceable(name="write_file", tags=["filesystem"])
def write_file_tool(path: str, content: str) -> str:
    """Write UTF-8 text content to a file and return a short status message."""
    written = write_text_file(path, content)
    size = Path(written).stat().st_size
    return f"OK: wrote {size} bytes to {written}"


@traceable(name="run_bash_command", tags=["filesystem"])
def run_bash(command: str, timeout: int = 60, cwd: str | Path | None = None) -> str:
    if len(command) > 1000:
        raise ValueError("Command too long (>1000 chars)")
    for banned in SAFE_BANNED_PATTERNS:
        if banned in command:
            raise ValueError(f"Dangerous command blocked: {banned}")

    result = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise ToolException(f"Command exited {result.returncode}:\n{output}")
    return output.strip()


@tool
@traceable(name="run_bash", tags=["filesystem"])
def run_bash_tool(command: str, timeout: int = 60) -> str:
    """Run a constrained shell command and return its combined output."""
    return run_bash(command, timeout=timeout)
