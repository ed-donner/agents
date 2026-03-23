from agents import Agent, output_guardrail, GuardrailFunctionOutput, RunContextWrapper
from models import BugFinding, BugDetectionOutput, BugGuardrailResult

def collect_violations(bugs: list[BugFinding]) -> list[str]:
    """
    Runs all three behavioural checks against the bug findings list and
    returns a list of violation messages. An empty list means all checks passed.
    """
    violations = []

    VAGUE_PHRASES = ["this might be a bug", "could be an issue", "may cause problems", "potential issue", "possible bug", "might fail", "unclear", "unknown", "needs review", "not sure"]


    vague_findings = []
    for bug in bugs:
        description_lower = bug.description.strip().lower()
        is_too_short = len(description_lower) < 20
        contains_vague_phrase = any(phrase in description_lower for phrase in VAGUE_PHRASES)

        if is_too_short or contains_vague_phrase:
            vague_findings.append(bug.file_path)

    if vague_findings:
        violations.append(
            f"Check 1 FAILED — Vague or uninformative descriptions detected in "
            f"{len(vague_findings)} finding(s): {', '.join(vague_findings)}. "
            f"Every description must clearly explain what the bug is and where it occurs."
        )

    CRITICAL_RATIO_THRESHOLD = 0.40
    MIN_FINDINGS_FOR_RATIO_CHECK = 5

    if len(bugs) >= MIN_FINDINGS_FOR_RATIO_CHECK:
        critical_count = sum(1 for bug in bugs if bug.severity == "CRITICAL")
        critical_ratio = critical_count / len(bugs)

        if critical_ratio == 1.0:
            violations.append(
                f"Check 2 FAILED — All {len(bugs)} findings are marked CRITICAL. "
                f"This indicates likely severity inflation or hallucination. "
                f"Re-evaluate severity levels — CRITICAL should be reserved for "
                f"bugs that cause data loss, crashes, or serious runtime failures."
            )
        elif critical_ratio > CRITICAL_RATIO_THRESHOLD:
            violations.append(
                f"Check 2 FAILED — {critical_count} out of {len(bugs)} findings "
                f"({critical_ratio:.0%}) are marked CRITICAL, exceeding the "
                f"{CRITICAL_RATIO_THRESHOLD:.0%} threshold. "
                f"Review severity assignments — not all bugs warrant CRITICAL severity."
            )

    INVALID_LINE_VALUES = {"", "n/a", "unknown", "none", "0", "null", "-"}

    missing_line_findings = []
    for bug in bugs:
        line_value = bug.line_number.strip().lower()
        if line_value in INVALID_LINE_VALUES:
            missing_line_findings.append(bug.file_path)

    if missing_line_findings:
        violations.append(
            f"Check 3 FAILED — Missing or invalid line numbers in "
            f"{len(missing_line_findings)} finding(s): {', '.join(missing_line_findings)}. "
            f"Every finding must reference a specific line or line range (e.g. '42' or '38-45')."
        )

    return violations


@output_guardrail
async def bug_detection_guardrail(
    ctx: RunContextWrapper, agent: Agent, output: BugDetectionOutput
) -> GuardrailFunctionOutput:
    """
    Output guardrail for the Bug Detection Agent.

    Runs three behavioural checks on the agent's findings:
      1. No vague or uninformative descriptions.
      2. No severity inflation (too many CRITICAL findings).
      3. No missing or invalid line numbers.
    """

    if not output.bugs:
        return GuardrailFunctionOutput(
            output_info=BugGuardrailResult(
                passed=True,
                reason="No bugs returned. Skipping behavioural checks."
            ),
            tripwire_triggered=False
        )

    violations = collect_violations(output.bugs)
    passed = len(violations) == 0

    if passed:
        reason = (
            f"All checks passed. {len(output.bugs)} finding(s) reviewed — "
            f"descriptions are specific, severity distribution is reasonable, "
            f"and all findings include valid line numbers."
        )
    else:
        reason = (
            f"{len(violations)} check(s) failed out of 3:\n" +
            "\n".join(f"  - {v}" for v in violations)
        )

    return GuardrailFunctionOutput(
        output_info=BugGuardrailResult(passed=passed, reason=reason),
        tripwire_triggered=not passed
    )