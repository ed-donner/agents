import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from agents import function_tool

load_dotenv(override=True)

REPORT_OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR") or "./reports"

@function_tool
def write_report_tool(
    code_map: list,
    bugs: list,
    refactor_suggestions: list,
    security_findings: list,
    total_files_reviewed: int,
    total_lines_analyzed: int
) -> dict:
    """Compiles all agent findings into a structured Markdown report and writes it to disk."""
    try:
        os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_review_report_{timestamp}.md"
        report_path = str(Path(REPORT_OUTPUT_DIR) / filename)

        critical_bugs = [b for b in bugs if b.get("severity") == "CRITICAL"]
        high_bugs = [b for b in bugs if b.get("severity") == "HIGH"]

        critical_security = [s for s in security_findings if s.get("severity") == "CRITICAL"]
        high_security = [s for s in security_findings if s.get("severity") == "HIGH"]

        high_refactor = [r for r in refactor_suggestions if r.get("priority") == "HIGH"]

        health_score = _compute_health_score(bugs, refactor_suggestions, security_findings)

        executive_summary = _build_executive_summary(
            total_files_reviewed, total_lines_analyzed,
            bugs, refactor_suggestions, security_findings, health_score
        )

        sections = [
            _header(timestamp),
            executive_summary,
            _bug_section(bugs),
            _refactor_section(refactor_suggestions),
            _security_section(security_findings),
            _files_table(code_map),
            _action_plan(critical_bugs, high_bugs, critical_security, high_security, high_refactor)
        ]

        report_content = "\n\n---\n\n".join(sections)

        Path(report_path).write_text(report_content, encoding="utf-8")

        return {
            "success": True,
            "report_path": report_path,
            "executive_summary": executive_summary,
            "error": ""
        }

    except Exception as e:
        return {
            "success": False,
            "report_path": "",
            "executive_summary": "",
            "error": f"Failed to write report: {str(e)}"
        }


def _header() -> str:
    return (
        f"# Code Review Report\n"
        f"_Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}_"
    )


def _build_executive_summary(
    total_files, total_lines, bugs, refactor_suggestions, security_findings, health_score
) -> str:
    critical_sec = sum(1 for s in security_findings if s.get("severity") == "CRITICAL")
    critical_bug = sum(1 for b in bugs if b.get("severity") == "CRITICAL")

    overall_note = (
        "The codebase has critical issues that require immediate attention."
        if (critical_sec > 0 or critical_bug > 0)
        else "The codebase is in reasonable shape with some areas for improvement."
        if health_score >= 6
        else "The codebase has a number of issues across multiple categories that should be addressed."
    )

    return (
        f"## 1. Executive Summary\n\n"
        f"| Metric | Value |\n"
        f"|---|---|\n"
        f"| Files Reviewed | {total_files} |\n"
        f"| Lines Analyzed | {total_lines:,} |\n"
        f"| Bugs Found | {len(bugs)} |\n"
        f"| Refactor Suggestions | {len(refactor_suggestions)} |\n"
        f"| Security Findings | {len(security_findings)} |\n"
        f"| Health Score | **{health_score}/10** |\n\n"
        f"{overall_note}"
    )


def _bug_section(bugs: list) -> str:
    if not bugs:
        return "## 2. Bug Findings\n\n✅ No bugs were found."

    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    lines = ["## 2. Bug Findings\n"]

    for severity in severity_order:
        group = [b for b in bugs if b.get("severity") == severity]
        if not group:
            continue
        lines.append(f"### {severity} ({len(group)})\n")
        for bug in group:
            lines.append(
                f"**File:** `{bug.get('file_path', 'N/A')}` — "
                f"**Line:** `{bug.get('line_number', 'N/A')}`\n\n"
                f"**Category:** {bug.get('category', 'N/A')}\n\n"
                f"**Description:** {bug.get('description', 'N/A')}\n\n"
                f"**Suggestion:** {bug.get('suggestion', 'N/A')}\n"
            )

    return "\n".join(lines)


def _refactor_section(suggestions: list) -> str:
    if not suggestions:
        return "## 3. Refactor Suggestions\n\n✅ No refactor suggestions were found."

    priority_order = ["HIGH", "MEDIUM", "LOW"]
    lines = ["## 3. Refactor Suggestions\n"]

    for priority in priority_order:
        group = [s for s in suggestions if s.get("priority") == priority]
        if not group:
            continue
        lines.append(f"### {priority} ({len(group)})\n")
        for suggestion in group:
            lines.append(
                f"**File:** `{suggestion.get('file_path', 'N/A')}` — "
                f"**Line:** `{suggestion.get('line_number', 'N/A')}`\n\n"
                f"**Category:** {suggestion.get('category', 'N/A')}\n\n"
                f"**Description:** {suggestion.get('description', 'N/A')}\n\n"
                f"**Suggestion:** {suggestion.get('suggestion', 'N/A')}\n"
            )

    return "\n".join(lines)


def _security_section(findings: list) -> str:
    if not findings:
        return "## 4. Security Vulnerabilities\n\n✅ No security vulnerabilities were found."

    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    lines = ["## 4. Security Vulnerabilities\n"]

    for severity in severity_order:
        group = [f for f in findings if f.get("severity") == severity]
        if not group:
            continue
        lines.append(f"### {severity} ({len(group)})\n")
        for finding in group:
            lines.append(
                f"**File:** `{finding.get('file_path', 'N/A')}` — "
                f"**Line:** `{finding.get('line_number', 'N/A')}`\n\n"
                f"**Category:** {finding.get('category', 'N/A')}\n\n"
                f"**Description:** {finding.get('description', 'N/A')}\n\n"
                f"**Recommendation:** {finding.get('recommendation', 'N/A')}\n"
            )

    return "\n".join(lines)


def _files_table(code_map: list) -> str:
    if not code_map:
        return "## 5. Files Reviewed\n\n_No file data available._"

    lines = [
        "## 5. Files Reviewed\n",
        "| File | Lines | Parse Status |",
        "|---|---|---|"
    ]

    for file in code_map:
        parse_status = "⚠️ Parse Error" if file.get("parse_error") else "✅ OK"
        lines.append(
            f"| `{file.get('file_path', 'N/A')}` "
            f"| {file.get('line_count', 0):,} "
            f"| {parse_status} |"
        )

    return "\n".join(lines)


def _action_plan(
    critical_bugs, high_bugs,
    critical_security, high_security,
    high_refactor
) -> str:
    lines = ["## 6. Recommended Action Plan\n"]
    step = 1
    added = set()

    def add_items(items, label_fn):
        nonlocal step
        for item in items:
            key = (item.get("file_path"), item.get("line_number"))
            if key not in added:
                lines.append(f"{step}. {label_fn(item)}")
                added.add(key)
                step += 1

    add_items(
        critical_security,
        lambda i: f"**[SECURITY CRITICAL]** Fix `{i.get('category')}` "
                  f"in `{i.get('file_path')}` line {i.get('line_number')}. "
                  f"{i.get('recommendation', '')}"
    )
    add_items(
        critical_bugs,
        lambda i: f"**[BUG CRITICAL]** Resolve `{i.get('category')}` "
                  f"in `{i.get('file_path')}` line {i.get('line_number')}. "
                  f"{i.get('suggestion', '')}"
    )
    add_items(
        high_security,
        lambda i: f"**[SECURITY HIGH]** Address `{i.get('category')}` "
                  f"in `{i.get('file_path')}` line {i.get('line_number')}."
    )
    add_items(
        high_bugs,
        lambda i: f"**[BUG HIGH]** Fix `{i.get('category')}` "
                  f"in `{i.get('file_path')}` line {i.get('line_number')}."
    )
    add_items(
        high_refactor,
        lambda i: f"**[REFACTOR HIGH]** Improve `{i.get('category')}` "
                  f"in `{i.get('file_path')}` line {i.get('line_number')}."
    )

    if step == 1:
        lines.append("No critical or high priority actions required. "
                     "Review medium and low findings at your discretion.")

    return "\n".join(lines)


def _compute_health_score(bugs: list, refactor_suggestions: list, security_findings: list) -> int:
    """Computes a health score out of 10 based on finding counts and severity."""
    score = 10.0

    severity_deductions = {"CRITICAL": 2.0, "HIGH": 1.0, "MEDIUM": 0.4, "LOW": 0.1}
    priority_deductions = {"HIGH": 0.5, "MEDIUM": 0.2, "LOW": 0.05}

    for bug in bugs:
        score -= severity_deductions.get(bug.get("severity", "LOW"), 0.1)

    for finding in security_findings:   
        score -= severity_deductions.get(finding.get("severity", "LOW"), 0.1) * 1.5

    for suggestion in refactor_suggestions:
        score -= priority_deductions.get(suggestion.get("priority", "LOW"), 0.05)

    return max(0, round(score))