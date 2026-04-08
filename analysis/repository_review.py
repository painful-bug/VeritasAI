from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analysis.core import (
    analyze_file,
    categorize_file,
    detect_language,
    is_review_candidate,
    extract_data_sources,
    identify_sensitive_fields,
    infer_schema_fields,
)
from tools.filesystem_tools import write_text_file
from utils.strings import shorten

_METADATA_PREFIX = "<!-- DIRECTORY_ANALYSIS_META "
_METADATA_SUFFIX = " -->"
_PRINTABLE_RATIO_MIN = 0.75
_BINARY_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
_DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".idea",
    ".vscode",
    ".chroma_db",
    "dist",
    "build",
}
_DEFAULT_EXCLUDED_GLOBS = {
    ".env",
    ".env.*",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.class",
    "*.jar",
    "*.whl",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.7z",
    "*.lock",
    ".DS_Store",
}
_STOPWORDS = {
    "about",
    "after",
    "agent",
    "analysis",
    "analyzes",
    "appears",
    "build",
    "built",
    "code",
    "compliance",
    "contains",
    "context",
    "data",
    "default",
    "details",
    "document",
    "documents",
    "file",
    "files",
    "folder",
    "function",
    "generated",
    "implements",
    "including",
    "likely",
    "logic",
    "model",
    "module",
    "path",
    "project",
    "python",
    "repository",
    "review",
    "reviewer",
    "source",
    "structured",
    "summary",
    "system",
    "text",
    "tool",
    "tools",
    "type",
    "used",
    "uses",
    "using",
    "workflow",
}
_DIRECTORY_PURPOSE_HINTS = {
    "analysis": "Core analysis and detection logic.",
    "config": "Configuration artifacts that tune runtime behavior.",
    "data": "Input datasets or tabular records consumed by the project.",
    "demo_violations": "Example fixtures and intentionally unsafe scenarios used to exercise detections.",
    "docs": "Supporting documentation and narrative context.",
    "graphs": "Workflow orchestration and graph composition.",
    "knowledge": "Knowledge-base assets used for retrieval.",
    "llm": "Model-provider setup and LLM-facing adapters.",
    "models": "Shared typed models and state definitions.",
    "nodes": "Graph node implementations and execution steps.",
    "prompts": "Prompt assets consumed by the agentic runtime.",
    "rag": "Retrieval and vector-store integration.",
    "scripts": "Operational or maintenance scripts.",
    "templates": "Rendered output templates or prompt scaffolding.",
    "tests": "Automated test coverage.",
    "tools": "Tool wrappers surfaced to agents or nodes.",
    "tracing": "Tracing, observability, and run metadata hooks.",
    "ui": "User-facing interface code.",
    "vscode-extension": "VS Code extension implementation and editor integration.",
}
_MAX_DIRECTORY_LINES = 24
_MAX_RELATIONSHIP_LINES = 12
_MAX_KEY_FILES = 18
_MAX_KEY_FILES_PER_DIRECTORY = 4


def resolve_workspace_root(target_path: str | Path) -> Path:
    candidate = Path(target_path).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    markers = ("config.yaml", "README.md", ".git", "package.json", "pyproject.toml")
    for parent in (candidate, *candidate.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent
    return candidate


def path_is_within_root(target_path: str | Path, root: str | Path) -> bool:
    try:
        candidate = Path(target_path).expanduser().resolve()
        workspace_root = Path(root).expanduser().resolve()
        candidate.relative_to(workspace_root)
        return True
    except Exception:
        return False


def _settings(config: dict[str, Any] | None) -> dict[str, Any]:
    effective = config or {}
    directory_analysis = effective.get("directory_analysis", {}) or {}
    output_dir = str(effective.get("scan", {}).get("output_dir", "compliance-analysis") or "compliance-analysis").strip()
    excluded_dirs = {str(item).strip() for item in directory_analysis.get("exclude_dirs", []) if str(item).strip()}
    excluded_globs = {str(item).strip() for item in directory_analysis.get("exclude_globs", []) if str(item).strip()}
    if output_dir:
        excluded_dirs.add(Path(output_dir).name)
    return {
        "enabled": bool(directory_analysis.get("enabled", True)),
        "filename": str(directory_analysis.get("filename", "DIRECTORY_ANALYSIS.md") or "DIRECTORY_ANALYSIS.md"),
        "preview_chars": max(1200, int(directory_analysis.get("preview_chars", 3000) or 3000)),
        "exclude_dirs": sorted(_DEFAULT_EXCLUDED_DIRS | excluded_dirs),
        "exclude_globs": sorted(_DEFAULT_EXCLUDED_GLOBS | excluded_globs),
    }


def analysis_path_for_root(root: str | Path, config: dict[str, Any] | None = None) -> Path:
    workspace_root = Path(root).expanduser().resolve()
    return workspace_root / _settings(config)["filename"]


def _matches_any(relative_path: str, patterns: list[str]) -> bool:
    candidate = relative_path.replace(os.sep, "/")
    return any(Path(candidate).match(pattern) for pattern in patterns)


def _should_skip_dir(path: Path, root: Path, settings: dict[str, Any]) -> bool:
    relative = path.relative_to(root).as_posix()
    if relative == ".":
        return False
    return path.name in settings["exclude_dirs"] or _matches_any(relative, settings["exclude_globs"])


def _should_skip_file(path: Path, root: Path, settings: dict[str, Any]) -> bool:
    relative = path.relative_to(root).as_posix()
    if path.name == settings["filename"]:
        return True
    return _matches_any(relative, settings["exclude_globs"])


def _is_binary_blob(blob: bytes) -> bool:
    if not blob:
        return False
    if b"\x00" in blob:
        return True
    printable = sum(1 for byte in blob if 32 <= byte <= 126 or byte in {9, 10, 13})
    return printable / max(len(blob), 1) < _PRINTABLE_RATIO_MIN


def _read_preview(path: Path, preview_chars: int) -> tuple[str, bool]:
    if path.suffix.lower() in _BINARY_DOCUMENT_EXTENSIONS:
        return "", False

    with path.open("rb") as handle:
        raw = handle.read(max(8192, preview_chars * 4))

    if _is_binary_blob(raw):
        return "", False

    text = raw.decode("utf-8", errors="replace")
    truncated = len(text) > preview_chars
    return text[:preview_chars], truncated


def _top_level_symbols(path: Path, content: str, language: str | None) -> list[str]:
    if not content:
        return []

    if language == "Python":
        try:
            module = ast.parse(content)
        except SyntaxError:
            return []
        return [
            node.name
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ][:12]

    if language in {"JavaScript", "TypeScript"}:
        matches = re.findall(
            r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)|class\s+([A-Za-z_][A-Za-z0-9_]*)|const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=",
            content,
        )
        symbols: list[str] = []
        for group in matches:
            for candidate in group:
                if candidate and candidate not in symbols:
                    symbols.append(candidate)
        return symbols[:12]

    return []


def _relative_if_within(candidate: Path, root: Path) -> str | None:
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except Exception:
        return None


def _resolve_python_import_candidates(current_path: Path, root: Path, module: str | None, level: int) -> list[str]:
    base_dir = current_path.parent
    if level > 0:
        for _ in range(max(level - 1, 0)):
            base_dir = base_dir.parent
    elif module:
        base_dir = root

    module_path = Path(*(module or "").split(".")) if module else Path()
    candidates = [
        base_dir / module_path.with_suffix(".py"),
        base_dir / module_path / "__init__.py",
    ]
    resolved = []
    for candidate in candidates:
        relative = _relative_if_within(candidate, root)
        if relative and candidate.exists():
            resolved.append(relative)
    return resolved


def _resolve_local_path_reference(raw_value: str, current_path: Path, root: Path) -> str | None:
    candidate = Path(raw_value)
    if not candidate.is_absolute():
        candidate = (current_path.parent / candidate).resolve()
    relative = _relative_if_within(candidate, root)
    return relative if relative and candidate.exists() else None


def _internal_references(path: Path, root: Path, content: str, language: str | None) -> list[str]:
    references: list[str] = []

    if language == "Python" and content:
        try:
            module = ast.parse(content)
        except SyntaxError:
            module = None
        if module is not None:
            for node in ast.walk(module):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        references.extend(_resolve_python_import_candidates(path, root, alias.name, 0))
                elif isinstance(node, ast.ImportFrom):
                    references.extend(_resolve_python_import_candidates(path, root, node.module, node.level))

    if language in {"JavaScript", "TypeScript"} and content:
        for raw_target in re.findall(r"(?:from|require\()\s*['\"]([^'\"]+)['\"]", content):
            if not raw_target.startswith("."):
                continue
            base = (path.parent / raw_target).resolve()
            candidates = [
                base,
                base.with_suffix(".ts"),
                base.with_suffix(".tsx"),
                base.with_suffix(".js"),
                base.with_suffix(".jsx"),
                base / "index.ts",
                base / "index.tsx",
                base / "index.js",
                base / "index.jsx",
            ]
            for candidate in candidates:
                relative = _relative_if_within(candidate, root)
                if relative and candidate.exists():
                    references.append(relative)
                    break

    for source in extract_data_sources(content):
        if source.get("source_type") != "local_path":
            continue
        resolved = _resolve_local_path_reference(str(source.get("url_or_path") or ""), path, root)
        if resolved:
            references.append(resolved)

    unique: list[str] = []
    for reference in references:
        if reference not in unique:
            unique.append(reference)
    return unique[:12]


def _entrypoint_hints(path: Path, content: str) -> bool:
    lowered = content.lower()
    return (
        path.name in {"app.py", "main.py", "run.py", "run_all.py", "mcp_server.py"}
        or "__name__ == \"__main__\"" in content
        or "__name__ == '__main__'" in content
        or "export function activate" in lowered
        or "def activate(" in lowered
    )


def _describe_directory(relative_dir: str, entries: list[dict[str, Any]]) -> str:
    if relative_dir == ".":
        return "Workspace root containing top-level project assets."
    directory_name = Path(relative_dir).name
    hinted = _DIRECTORY_PURPOSE_HINTS.get(directory_name)
    if hinted:
        return hinted

    categories = Counter(entry["file_type"] for entry in entries)
    dominant = categories.most_common(1)[0][0].replace("_", " ") if categories else "mixed content"
    return f"{directory_name} primarily contains {dominant}."


def _theme_terms(entries: list[dict[str, Any]], readme_excerpt: str) -> list[str]:
    counter: Counter[str] = Counter()
    corpus_parts = [readme_excerpt]
    corpus_parts.extend(entry["summary"] for entry in entries)
    corpus_parts.extend(entry["relative_path"].replace("/", " ") for entry in entries)
    for part in corpus_parts:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", part.lower()):
            normalized = token.strip("_-")
            if normalized in _STOPWORDS or normalized.isdigit():
                continue
            counter[normalized] += 1
    return [term for term, _ in counter.most_common(8)]


def _readme_excerpt(root: Path, preview_chars: int) -> str:
    for candidate in (root / "README.md", root / "README.rst", root / "README.txt"):
        if not candidate.exists():
            continue
        text, _ = _read_preview(candidate, preview_chars)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        prose = [line for line in lines if not line.startswith("#")]
        if prose:
            return shorten(" ".join(prose[:6]), 400)
    return ""


def _snapshot(root: Path, settings: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], str]:
    files: list[dict[str, Any]] = []
    directories: set[str] = {"."}

    for current_dir, dirnames, filenames in os.walk(root):
        current_path = Path(current_dir)
        relative_dir = current_path.relative_to(root).as_posix() if current_path != root else "."
        directories.add(relative_dir)

        kept_dirs = []
        for dirname in sorted(dirnames):
            candidate = current_path / dirname
            if _should_skip_dir(candidate, root, settings):
                continue
            kept_dirs.append(dirname)
            directories.add(candidate.relative_to(root).as_posix())
        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            path = current_path / filename
            if _should_skip_file(path, root, settings):
                continue
            if not is_review_candidate(path):
                continue
            stat = path.stat()
            files.append(
                {
                    "path": path,
                    "relative_path": path.relative_to(root).as_posix(),
                    "size": int(stat.st_size),
                    "mtime_ns": int(stat.st_mtime_ns),
                }
            )

    digest = hashlib.sha256()
    for item in files:
        digest.update(
            f"{item['relative_path']}|{item['size']}|{item['mtime_ns']}\n".encode("utf-8", errors="ignore")
        )
    return files, sorted(directories), digest.hexdigest()


def _parse_metadata(markdown: str) -> dict[str, Any] | None:
    first_line = (markdown or "").splitlines()[0] if markdown else ""
    if not first_line.startswith(_METADATA_PREFIX) or not first_line.endswith(_METADATA_SUFFIX):
        return None
    try:
        return json.loads(first_line[len(_METADATA_PREFIX) : -len(_METADATA_SUFFIX)])
    except json.JSONDecodeError:
        return None


def _strip_metadata(markdown: str) -> str:
    lines = (markdown or "").splitlines()
    if lines and lines[0].startswith(_METADATA_PREFIX) and lines[0].endswith(_METADATA_SUFFIX):
        return "\n".join(lines[1:]).lstrip()
    return markdown


def _entry_summary(path: Path, root: Path, preview_chars: int) -> dict[str, Any]:
    relative_path = path.relative_to(root).as_posix()
    preview, truncated = _read_preview(path, preview_chars)
    file_type = categorize_file(path, preview)
    language = detect_language(path)
    analysis_result, _ = analyze_file(
        file_path=str(path),
        file_type=file_type,
        file_content=preview,
        config={"rag": {"top_k": 1}},
        query_rag=None,
    )
    fields = infer_schema_fields(preview, path, file_type) if preview else []
    data_sources = extract_data_sources(preview) if preview else []
    local_references = _internal_references(path, root, preview, language)
    symbols = _top_level_symbols(path, preview, language)
    sensitive_fields = identify_sensitive_fields(" ".join(fields) + "\n" + preview[:4000]) if preview else []

    return {
        "relative_path": relative_path,
        "directory": str(Path(relative_path).parent).replace("\\", "/") if "/" in relative_path else ".",
        "file_type": file_type,
        "language": language,
        "size": int(path.stat().st_size),
        "summary": shorten(analysis_result["summary"], 140),
        "predicted_output": shorten(analysis_result["predicted_output"] or "", 140),
        "fields": fields[:12],
        "data_sources": data_sources[:8],
        "internal_references": local_references,
        "symbols": symbols,
        "sensitive_fields": sorted(set(sensitive_fields))[:8],
        "preview_excerpt": shorten(preview, 220) if preview else "",
        "truncated": truncated,
        "is_entrypoint": _entrypoint_hints(path, preview),
    }


def _entry_priority(entry: dict[str, Any]) -> tuple[int, int, str]:
    score = 0
    if entry["is_entrypoint"]:
        score += 6
    score += min(len(entry["internal_references"]), 3) * 2
    if entry["data_sources"]:
        score += 4
    if entry["sensitive_fields"]:
        score += 3
    if entry["fields"]:
        score += 2
    if entry["file_type"] == "source_code":
        score += 1
    return (-score, len(entry["relative_path"]), entry["relative_path"])


def _key_files(entries: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(entries) <= limit:
        return sorted(entries, key=lambda entry: entry["relative_path"])
    selected = sorted(entries, key=_entry_priority)[:limit]
    return sorted(selected, key=lambda entry: entry["relative_path"])


def _compact_list(values: list[str], limit: int = 4) -> str:
    return ", ".join(f"`{value}`" for value in values[:limit])


def _format_file_highlight(entry: dict[str, Any]) -> str:
    details = [entry["summary"]]
    if entry["is_entrypoint"]:
        details.append("entrypoint")
    if entry["internal_references"]:
        details.append(f"refs: {_compact_list(entry['internal_references'], limit=3)}")
    elif entry["data_sources"]:
        sources = [str(item.get("url_or_path") or "") for item in entry["data_sources"] if item.get("url_or_path")]
        if sources:
            details.append(f"data: {_compact_list(sources, limit=2)}")
    elif entry["fields"]:
        details.append(f"fields: {_compact_list(entry['fields'], limit=4)}")
    return f"- `{entry['relative_path']}`: {' | '.join(part for part in details if part)}"


def _render_markdown(
    root: Path,
    entries: list[dict[str, Any]],
    directories: list[str],
    snapshot_hash: str,
    generated_at: str,
    preview_chars: int,
) -> str:
    directory_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        directory_map[entry["directory"]].append(entry)

    readme_excerpt = _readme_excerpt(root, preview_chars)
    theme_terms = _theme_terms(entries, readme_excerpt)
    languages = Counter(entry["language"] or "Unknown" for entry in entries if entry["file_type"] == "source_code")
    file_types = Counter(entry["file_type"] for entry in entries)
    entrypoints = [entry["relative_path"] for entry in entries if entry["is_entrypoint"]][:8]
    relationship_lines: list[str] = []
    for entry in _key_files(entries, limit=max(_MAX_RELATIONSHIP_LINES * 2, _MAX_KEY_FILES)):
        if not entry["internal_references"]:
            continue
        relationship_lines.append(
            f"- `{entry['relative_path']}` -> {', '.join(f'`{item}`' for item in entry['internal_references'][:3])}"
        )
        if len(relationship_lines) >= _MAX_RELATIONSHIP_LINES:
            break

    overview = readme_excerpt or (
        "The repository appears to be a "
        f"{', '.join(language for language, _ in languages.most_common(3)) or 'mixed-language'} project "
        f"focused on {', '.join(theme_terms[:4]) or 'application logic and data processing'}."
    )

    key_entries = _key_files(entries, limit=_MAX_KEY_FILES)

    lines = [
        "# Directory Analysis",
        "",
        f"Generated: `{generated_at}`",
        f"Workspace root: `{root}`",
        f"Snapshot hash: `{snapshot_hash}`",
        f"Files analysed: `{len(entries)}`",
        f"Directories analysed: `{len(directories)}`",
        "",
        "## Repository Overview",
        "",
        f"- Purpose: {shorten(overview, 220)}",
        f"- Main themes: {', '.join(theme_terms[:6]) if theme_terms else 'No dominant themes inferred.'}",
        f"- Dominant languages: {', '.join(f'{name} ({count})' for name, count in languages.most_common(5)) or 'No source code detected.'}",
        f"- File type mix: {', '.join(f'{name} ({count})' for name, count in file_types.most_common(6))}",
        f"- Likely entrypoints: {', '.join(f'`{path}`' for path in entrypoints) if entrypoints else 'None inferred.'}",
        "",
        "## Directory Map",
        "",
    ]

    for relative_dir in directories[:_MAX_DIRECTORY_LINES]:
        child_entries = directory_map.get(relative_dir, [])
        if relative_dir == ".":
            immediate_children = sorted(
                {
                    entry["relative_path"].split("/", 1)[0]
                    for entry in entries
                    if entry["relative_path"]
                }
            )
        else:
            prefix = f"{relative_dir}/"
            immediate_children = sorted(
                {
                    suffix.split("/", 1)[0]
                    for entry in entries
                    if entry["relative_path"].startswith(prefix)
                    for suffix in [entry["relative_path"][len(prefix) :]]
                    if suffix
                }
            )
        dominant_languages = Counter(entry["language"] or "Unknown" for entry in child_entries if entry["language"])
        key_paths = ", ".join(
            f"`{entry['relative_path']}`" for entry in _key_files(child_entries, limit=_MAX_KEY_FILES_PER_DIRECTORY)
        )
        lines.append(
            (
                f"- `{relative_dir}`: {_describe_directory(relative_dir, child_entries)} "
                f"Files=`{len(child_entries)}`. "
                f"Languages={', '.join(f'{name} ({count})' for name, count in dominant_languages.most_common(3)) or 'None'}. "
                f"Children={', '.join(f'`{name}`' for name in immediate_children[:8]) or 'None'}. "
                f"Key files={key_paths or 'None'}"
            )
        )
    if len(directories) > _MAX_DIRECTORY_LINES:
        lines.extend(["", f"- Additional directories omitted from the summary: `{len(directories) - _MAX_DIRECTORY_LINES}`"])
    lines.append("")

    if relationship_lines:
        lines.extend(["## Cross-file Relationships", "", *relationship_lines, ""])

    lines.extend(["## Key Files", ""])
    lines.extend(_format_file_highlight(entry) for entry in key_entries)
    omitted_count = max(len(entries) - len(key_entries), 0)
    if omitted_count:
        lines.extend(["", f"- Additional files omitted from the summary: `{omitted_count}`"])

    return "\n".join(lines).strip() + "\n"


def ensure_directory_analysis(
    target_path: str | Path,
    config: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    settings = _settings(config)
    workspace_root = resolve_workspace_root(target_path)
    analysis_path = analysis_path_for_root(workspace_root, config)

    if not settings["enabled"]:
        return {
            "workspace_root": str(workspace_root),
            "analysis_path": str(analysis_path),
            "content": "",
            "updated": False,
            "snapshot_hash": "",
            "file_count": 0,
            "directory_count": 0,
        }

    files, directories, snapshot_hash = _snapshot(workspace_root, settings)
    if analysis_path.exists() and not force:
        existing = analysis_path.read_text(encoding="utf-8")
        metadata = _parse_metadata(existing)
        if metadata and metadata.get("snapshot_hash") == snapshot_hash:
            return {
                "workspace_root": str(workspace_root),
                "analysis_path": str(analysis_path),
                "content": _strip_metadata(existing),
                "updated": False,
                "snapshot_hash": snapshot_hash,
                "file_count": int(metadata.get("file_count", len(files)) or len(files)),
                "directory_count": int(metadata.get("directory_count", len(directories)) or len(directories)),
            }

    entries = [_entry_summary(item["path"], workspace_root, settings["preview_chars"]) for item in files]
    generated_at = datetime.now(timezone.utc).isoformat()
    metadata = {
        "version": 1,
        "generated_at": generated_at,
        "workspace_root": str(workspace_root),
        "snapshot_hash": snapshot_hash,
        "file_count": len(entries),
        "directory_count": len(directories),
    }
    markdown = _render_markdown(
        root=workspace_root,
        entries=entries,
        directories=directories,
        snapshot_hash=snapshot_hash,
        generated_at=generated_at,
        preview_chars=settings["preview_chars"],
    )
    full_content = f"{_METADATA_PREFIX}{json.dumps(metadata, ensure_ascii=True)}{_METADATA_SUFFIX}\n\n{markdown}"
    write_text_file(analysis_path, full_content)
    return {
        "workspace_root": str(workspace_root),
        "analysis_path": str(analysis_path),
        "content": markdown,
        "updated": True,
        "snapshot_hash": snapshot_hash,
        "file_count": len(entries),
        "directory_count": len(directories),
    }
