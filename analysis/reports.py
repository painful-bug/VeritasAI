from __future__ import annotations

from pathlib import Path

from models.state import FileResult

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def build_file_report_markdown(file_result: FileResult) -> str:
    findings = sorted(file_result.get("findings", []), key=lambda item: SEVERITY_ORDER.get(item["severity"], 99))
    agentic_grade = file_result.get("agentic_grade")
    retrieval_evidence = file_result.get("retrieval_evidence", [])
    web_evidence = file_result.get("web_search_evidence", [])
    lines = [
        f"# Compliance Report: {file_result['file_path']}",
        f"**Status:** {file_result['status']}  |  **Findings:** {len(findings)}",
        f"**Summary:** {file_result['summary']}",
    ]

    if isinstance(agentic_grade, dict):
        lines.extend(
            [
                "",
                "## Agentic Self-Grade",
                (
                    f"**Relevancy:** {float(agentic_grade.get('relevancy', 0.0)):.2f}  |  "
                    f"**Faithfulness:** {float(agentic_grade.get('faithfulness', 0.0)):.2f}  |  "
                    f"**Context Quality:** {float(agentic_grade.get('context_quality', 0.0)):.2f}"
                ),
                (
                    f"**Needs Web Search:** {bool(agentic_grade.get('needs_web_search', False))}  |  "
                    f"**Retrieval Confidence:** {float(agentic_grade.get('retrieval_confidence', 0.0)):.2f}  |  "
                    f"**Trust Level:** {agentic_grade.get('trust_level', 'low')}"
                ),
                f"**Explanation:** {agentic_grade.get('explanation', '')}",
            ]
        )

    if retrieval_evidence:
        lines.extend(["", "## Retrieval Evidence"])
        for item in retrieval_evidence[:5]:
            if not isinstance(item, dict):
                continue
            lines.append(
                (
                    f"- chunk={item.get('chunk_id', '') or 'n/a'} page={item.get('page', 0)} "
                    f"confidence={float(item.get('confidence', 0.0)):.2f} "
                    f"trust={float(item.get('trust_score', 0.0)):.2f}"
                )
            )

    if web_evidence:
        lines.extend(["", "## Web Augmentation Evidence"])
        for item in web_evidence[:5]:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- {item.get('title', 'web result')} ({item.get('source', 'web')}): {item.get('url', '')}"
            )

    lines.extend(
        [
        "",
        "## Findings",
    ]
    )
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
