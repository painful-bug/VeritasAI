from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from analysis.core import report_filename_for
from models.state import FileResult, Finding
from utils.strings import shorten

STATUS_ORDER = {"FAIL": 0, "WARN": 1, "ERROR": 2, "PASS": 3, "SKIPPED": 4}
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _severity_counts(file_results: list[FileResult]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for result in file_results:
        for finding in result.get("findings", []):
            counter[finding["severity"]] += 1
    return counter


def _recommendation_for_finding(finding: Finding) -> str:
    title = finding["title"].lower()
    if "biometric" in title:
        return "Pause deployment until the biometric use case, lawful basis, and authorization boundary are documented and approved."
    if "employment" in title or "hiring" in title:
        return "Remove protected attributes from model features or document the lawful basis, fairness analysis, and human review path before any deployment."
    if "credit" in title or "eligibility" in title:
        return "Document adverse-impact controls and remove sensitive features from automated eligibility or scoring logic unless a compliant exception clearly applies."
    if "scraped" in title or "data source" in title:
        return "Review provenance, terms of use, and consent evidence for the referenced dataset before continuing training or ingestion."
    if "sensitive" in title:
        return "Add minimization, masking, retention, and access controls around the sensitive data flow before the pipeline is used in production."
    if "governance" in title or "oversight" in title:
        return "Add logging, review, and human-oversight controls so consequential model outputs can be audited and challenged."
    return "Document the control, mitigation, or architectural change needed to eliminate the risk before release."


def _format_rag_citation(chunk_id: str | None, page: int | None) -> str:
    if chunk_id and page:
        return f"`{chunk_id}` on page {page}"
    if chunk_id:
        return f"`{chunk_id}`"
    if page:
        return f"page {page}"
    return "None recorded"


def build_file_report_markdown(file_result: FileResult) -> str:
    findings = sorted(file_result.get("findings", []), key=lambda item: SEVERITY_ORDER.get(item["severity"], 99))
    data_sources = file_result.get("data_sources", [])
    lines = [
        f"# Analysis Report - {Path(file_result['file_path']).name}",
        "",
        "## File Overview",
        f"- Path: `{file_result['file_path']}`",
        f"- Type: `{file_result['file_type']}`",
        f"- Language: `{file_result['language'] or 'n/a'}`",
        f"- Status: `{file_result['status']}`",
        "",
        "## Summary",
        file_result.get("summary") or "No summary available.",
        "",
        "## Predicted Output / Real-World Effect",
        file_result.get("predicted_output") or "Not applicable for this file type.",
        "",
        "## Findings",
    ]

    if not findings:
        lines.append("No findings were identified during this pass.")
    else:
        for finding in findings:
            regulations = ", ".join(finding.get("regulations", [])) or "None cited"
            jurisdictions = ", ".join(finding.get("jurisdictions", [])) or "Unspecified"
            lines.extend(
                [
                    f"### {finding['id']} - {finding['title']} ({finding['severity']})",
                    f"- Section: {finding['section_desc']}",
                    f"- Regulations: {regulations}",
                    f"- Jurisdictions: {jurisdictions}",
                    f"- Explanation: {finding['explanation']}",
                    f"- Knowledge base citation: {_format_rag_citation(finding.get('rag_chunk_id'), finding.get('rag_page'))}",
                    f"- Recommended action: {_recommendation_for_finding(finding)}",
                    "",
                ]
            )

    lines.extend(["## Data Sources", ""])
    if not data_sources:
        lines.append("No external or local data sources were detected in this file.")
    else:
        lines.append("| Source | Type | Verdict | Key Concern | KB Citation |")
        lines.append("|---|---|---|---|---|")
        for source in data_sources:
            concern = shorten("; ".join(source.get("concerns", [])) or source.get("description", ""), 100)
            citation = "None recorded"
            if source.get("rag_citations"):
                first_citation = source["rag_citations"][0]
                citation = _format_rag_citation(first_citation.get("chunk_id"), first_citation.get("page"))
            lines.append(
                f"| `{source['url_or_path']}` | `{source['source_type']}` | `{source['verdict']}` | {concern or 'None'} | {citation} |"
            )
            lines.append(f"| Citation |  |  | {citation} |")

    notes = file_result.get("notes", [])
    lines.extend(["", "## Notes", ""])
    if notes:
        lines.extend(f"- {note}" for note in notes)
    else:
        lines.append("- None.")

    return "\n".join(lines).strip() + "\n"


def build_report_context(
    target_directory: str,
    file_results: list[FileResult],
    llm_provider: str,
    llm_model: str,
) -> dict[str, Any]:
    ordered_results = sorted(
        file_results,
        key=lambda result: (STATUS_ORDER.get(result["status"], 99), -len(result.get("findings", [])), result["file_path"].lower()),
    )
    status_counts = Counter(result["status"] for result in ordered_results)
    severity_counts = _severity_counts(ordered_results)
    jurisdictions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    data_sources: list[dict[str, Any]] = []

    for result in ordered_results:
        for source in result.get("data_sources", []):
            data_sources.append({"source": source, "file_path": result["file_path"]})
        for finding in result.get("findings", []):
            if finding.get("jurisdictions"):
                for jurisdiction in finding["jurisdictions"]:
                    jurisdictions[jurisdiction].append({"file_path": result["file_path"], "finding": finding})
            else:
                jurisdictions["Global"].append({"file_path": result["file_path"], "finding": finding})

    critical_findings = [
        {"file_path": result["file_path"], "finding": finding}
        for result in ordered_results
        for finding in result.get("findings", [])
        if finding["severity"] == "HIGH"
    ]

    recommendations = [
        {
            "priority": index + 1,
            "file_path": result["file_path"],
            "severity": finding["severity"],
            "text": _recommendation_for_finding(finding),
        }
        for index, (result, finding) in enumerate(
            sorted(
                ((result, finding) for result in ordered_results for finding in result.get("findings", [])),
                key=lambda item: (SEVERITY_ORDER.get(item[1]["severity"], 99), item[0]["file_path"].lower()),
            )
        )
    ]

    executive_summary = _build_executive_summary(target_directory, ordered_results, status_counts)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_directory": target_directory,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "file_results": ordered_results,
        "status_counts": dict(status_counts),
        "severity_counts": dict(severity_counts),
        "jurisdictions": dict(sorted(jurisdictions.items(), key=lambda item: len(item[1]), reverse=True)),
        "data_sources": data_sources,
        "critical_findings": critical_findings,
        "recommendations": recommendations,
        "executive_summary": executive_summary,
    }


def _build_executive_summary(target_directory: str, file_results: list[FileResult], status_counts: Counter[str]) -> str:
    total = len(file_results)
    fail_count = status_counts.get("FAIL", 0)
    warn_count = status_counts.get("WARN", 0)
    if fail_count:
        top_fail = next((result for result in file_results if result["status"] == "FAIL"), None)
        lead = f"{fail_count} of the {total} reviewed files contain high-severity or fail-grade concerns."
        if top_fail and top_fail.get("findings"):
            lead += f" The most urgent issue is in {Path(top_fail['file_path']).name}: {top_fail['findings'][0]['title'].lower()}."
    elif warn_count:
        lead = f"No fail-grade files were identified, but {warn_count} of the {total} reviewed files require follow-up before production use."
    else:
        lead = f"The {total} reviewed files show no fail-grade or warning-level issues in this scan."

    return f"{lead} Target directory: `{target_directory}`. The scan favors deterministic evidence from file contents and flags controls that are missing or unclear."


def build_final_report_markdown(context: dict[str, Any]) -> str:
    file_results: list[FileResult] = context["file_results"]
    total_files = len(file_results)
    status_counts = Counter(context["status_counts"])
    severity_counts = Counter(context["severity_counts"])

    lines = [
        "# Final Compliance Report",
        "",
        "## Executive Summary",
        context["executive_summary"],
        "",
        "## Overall Results",
        "",
        "| Status | Count | % of Files |",
        "|---|---:|---:|",
    ]
    for status in ["PASS", "WARN", "FAIL", "ERROR", "SKIPPED"]:
        count = status_counts.get(status, 0)
        percent = (count / total_files * 100) if total_files else 0.0
        lines.append(f"| {status} | {count} | {percent:.1f}% |")
    lines.extend(
        [
            "",
            f"Findings by severity: HIGH={severity_counts.get('HIGH', 0)}, MEDIUM={severity_counts.get('MEDIUM', 0)}, LOW={severity_counts.get('LOW', 0)}.",
            "",
            "## Files Scanned",
            "",
            "| File | Type | Status | Findings | Report |",
            "|---|---|---|---:|---|",
        ]
    )
    for result in file_results:
        report_name = Path(result["report_path"]).name if result.get("report_path") else "—"
        lines.append(
            f"| `{result['file_path']}` | `{result['file_type']}` | `{result['status']}` | {len(result.get('findings', []))} | {report_name} |"
        )

    lines.extend(["", "## Critical Findings", ""])
    critical_findings = context.get("critical_findings", [])
    if not critical_findings:
        lines.append("No high-severity findings were identified in this scan.")
    else:
        for item in critical_findings:
            finding = item["finding"]
            lines.extend(
                [
                    f"### {Path(item['file_path']).name} - {finding['title']}",
                    f"- Severity: {finding['severity']}",
                    f"- Section: {finding['section_desc']}",
                    f"- Regulations: {', '.join(finding.get('regulations', [])) or 'None cited'}",
                    f"- Explanation: {finding['explanation']}",
                    f"- Knowledge base citation: {_format_rag_citation(finding.get('rag_chunk_id'), finding.get('rag_page'))}",
                    f"- Remediation: {_recommendation_for_finding(finding)}",
                    "",
                ]
            )

    lines.extend(["## Findings by Jurisdiction", ""])
    jurisdictions = context.get("jurisdictions", {})
    if not jurisdictions:
        lines.append("No jurisdiction-specific findings were generated.")
    else:
        for jurisdiction, entries in jurisdictions.items():
            lines.append(f"### {jurisdiction}")
            for entry in sorted(entries, key=lambda item: SEVERITY_ORDER.get(item["finding"]["severity"], 99)):
                finding = entry["finding"]
                lines.append(f"- `{entry['file_path']}`: {finding['severity']} - {finding['title']}. {shorten(finding['explanation'], 180)}")
            lines.append("")

    lines.extend(["## Data Source Validation Summary", ""])
    if not context.get("data_sources"):
        lines.append("No external or local data sources were identified during this scan.")
    else:
        lines.append("| Source | Referenced In | Type | Verdict | Key Concern | KB Citation |")
        lines.append("|---|---|---|---|---|---|")
        for item in context["data_sources"]:
            source = item["source"]
            concern = shorten("; ".join(source.get("concerns", [])) or source.get("description", ""), 120)
            citation = "None recorded"
            if source.get("rag_citations"):
                first_citation = source["rag_citations"][0]
                citation = _format_rag_citation(first_citation.get("chunk_id"), first_citation.get("page"))
            lines.append(
                f"| `{source['url_or_path']}` | `{Path(item['file_path']).name}` | `{source['source_type']}` | `{source['verdict']}` | {concern or 'None'} | {citation} |"
            )

    lines.extend(["", "## Prioritized Recommendations", ""])
    if not context.get("recommendations"):
        lines.append("1. Preserve the current controls and keep the knowledge base current so future scans remain meaningful.")
    else:
        for recommendation in context["recommendations"]:
            lines.append(
                f"{recommendation['priority']}. **[{recommendation['severity']}] `{Path(recommendation['file_path']).name}`:** {recommendation['text']}"
            )

    lines.extend(["", "## Appendix - Per-File Analysis Reports", ""])
    for result in file_results:
        report_name = Path(result["report_path"]).name if result.get("report_path") else report_filename_for(result["file_path"])
        lines.append(f"- `{report_name}` - {result['status']} ({len(result.get('findings', []))} findings)")

    return "\n".join(lines).strip() + "\n"


def build_final_report_html(context: dict[str, Any], templates_dir: str | Path) -> str:
    environment = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
    )
    template = environment.get_template("report.html.j2")
    return template.render(**context)
