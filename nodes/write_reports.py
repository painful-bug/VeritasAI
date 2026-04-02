from __future__ import annotations

from pathlib import Path

from analysis.reports import build_final_report_html, build_final_report_markdown, build_report_context
from models.events import progress_event
from models.state import ComplianceState
from tools.filesystem_tools import write_text_file
from utils.compat import traceable


@traceable(name="write_reports", tags=["compliance-scan", "reporting"])
def write_reports_node(state: ComplianceState) -> dict:
    output_dir = Path(state.get("_analysis_output_dir") or Path(state["target_directory"]) / state["config"].get("scan", {}).get("output_dir", "compliance-analysis"))
    output_dir.mkdir(parents=True, exist_ok=True)

    deduped_results = state.get("_deduped_file_results") or list({result["file_path"]: result for result in state.get("file_results", [])}.values())
    report_context = build_report_context(
        target_directory=state["target_directory"],
        file_results=deduped_results,
        llm_provider=state["llm_provider"],
        llm_model=state["llm_model"],
    )

    markdown = build_final_report_markdown(report_context)
    html = build_final_report_html(report_context, templates_dir=Path(__file__).resolve().parents[1] / "templates")

    md_path = output_dir / "final_compliance_report.md"
    html_path = output_dir / "final_compliance_report.html"
    write_text_file(md_path, markdown, lock_timeout=int(state["config"].get("filesystem", {}).get("write_lock_timeout_s", 30)))
    write_text_file(html_path, html, lock_timeout=int(state["config"].get("filesystem", {}).get("write_lock_timeout_s", 30)))

    return {
        "final_report_md": markdown,
        "final_report_html": html,
        "scan_complete": True,
        "progress_events": [
            progress_event(
                "scan_complete",
                message="Final compliance reports written.",
                metadata={"markdown": str(md_path), "html": str(html_path), "files": len(deduped_results)},
            )
        ],
    }
