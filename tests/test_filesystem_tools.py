from __future__ import annotations

from pathlib import Path

import pytest

from tools.filesystem_tools import read_text_file, safe_resolve_path


def test_safe_resolve_path_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_resolve_path(tmp_path / ".." / ".." / "etc" / "passwd", allowed_root=tmp_path)


def test_read_text_file_returns_binary_placeholder(tmp_path: Path) -> None:
    file_path = tmp_path / "image.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00fake")

    content = read_text_file(file_path)

    assert content.startswith("<binary file:")
