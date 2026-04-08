from __future__ import annotations

from pathlib import Path

import nodes.review_repository as review_repository_module


def _base_state(file_path: str, workspace_root: str | None, restrict: bool) -> dict:
    return {
        "file_path": file_path,
        "file_content": "print('ok')\n",
        "config": {},
        "llm_provider": "openrouter",
        "llm_model": "nvidia/nemotron-3-super-120b-a12b:free",
        "opened_workspace_root": workspace_root,
        "restrict_directory_analysis_to_workspace": restrict,
        "file_result": None,
        "progress_events": [],
        "final_report_md": None,
        "scan_complete": False,
        "scan_error": None,
        "langsmith_run_id": None,
        "langsmith_run_url": None,
    }


def test_review_repository_node_skips_directory_analysis_for_files_outside_open_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    file_path = tmp_path / "outside.py"
    file_path.write_text("print('outside')\n", encoding="utf-8")
    called = False

    monkeypatch.setattr(review_repository_module, "dispatch_custom_event", lambda *args, **kwargs: None)

    def fake_ensure_directory_analysis(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("ensure_directory_analysis should not run for files outside the open workspace")

    monkeypatch.setattr(review_repository_module, "ensure_directory_analysis", fake_ensure_directory_analysis)

    result = review_repository_module.review_repository_node(
        _base_state(str(file_path), str(workspace_root), True),
        config={},
    )

    assert called is False
    assert result["agentic_context"] == ""
    assert result["directory_analysis_path"] is None


def test_review_repository_node_uses_open_workspace_root_when_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    nested = workspace_root / "src"
    nested.mkdir()
    file_path = nested / "inside.py"
    file_path.write_text("print('inside')\n", encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(review_repository_module, "dispatch_custom_event", lambda *args, **kwargs: None)

    def fake_ensure_directory_analysis(target_path, config=None, force=False):
        captured["target_path"] = target_path
        return {
            "analysis_path": str(workspace_root / "DIRECTORY_ANALYSIS.md"),
            "content": "# Directory Analysis\n",
            "updated": False,
            "file_count": 1,
            "directory_count": 2,
            "workspace_root": str(workspace_root),
        }

    monkeypatch.setattr(review_repository_module, "ensure_directory_analysis", fake_ensure_directory_analysis)

    result = review_repository_module.review_repository_node(
        _base_state(str(file_path), str(workspace_root), True),
        config={},
    )

    assert captured["target_path"] == str(workspace_root)
    assert result["workspace_root"] == str(workspace_root)
    assert result["agentic_context"] == "# Directory Analysis\n"
