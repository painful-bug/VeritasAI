from __future__ import annotations

from pathlib import Path

from models.state import FileResult

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def build_file_report_markdown(file_result: FileResult) -> str:
    findings = sorted(file_result.get("findings", []), key=lambda item: SEVERITY_ORDER.get(item["severity"], 99))
    lines = [
        f"# Compliance Report: {file_result['file_path']}",
        f"**Status:** {file_result['status']}  |  **Findings:** {len(findings)}",
        f"**Summary:** {file_result['summary']}",
        "",
        "## Findings",
    ]
    if not findings:
        lines.append("None found.")
    else:
        for index, finding in enumerate(findings, start=1):
            lines.extend(
                [
                    f"### {index}. [{finding['severity']}] {finding['regulation_name']}",
                    f"**Lines:** {finding['start_line']}–{finding['end_line']}  |  **Jurisdiction:** {finding['jurisdiction']}",
                    f"**Issue:** {finding['explanation']}",
                    f"**Remedy:** {finding['remedy']}",
                    "",
                ]
            )
    return "\n".join(lines).strip() + "\n"


def build_final_report_markdown(file_results: list[FileResult]) -> str:
    lines = [
        "# AI Ethics Compliance — Final Report",
        "",
        "## Summary Table",
        "",
        "| File | Status | Findings |",
        "|---|---|---:|",
    ]
    for result in file_results:
        lines.append(f"| `{Path(result['file_path']).name}` | {result['status']} | {len(result.get('findings', []))} |")
    lines.extend(["", "## Full Findings by File", ""])
    for result in file_results:
        lines.append(f"### {result['file_path']}")
        lines.append(build_file_report_markdown(result))
    return "\n".join(lines).strip() + "\n"
