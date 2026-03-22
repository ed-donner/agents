from agents import Agent, output_guardrail, GuardrailFunctionOutput, RunContextWrapper
from models import SecurityFinding, SecurityAuditOutput, SecurityGuardrailResult
import re

# ── Secret Pattern Registry ───────────────────────────────────────────────────
# Used by Check 3 to detect whether actual secret values have been echoed
# back into the findings. These patterns cover the most common secret formats.
# We scan both the description and recommendation fields of every finding.

SECRET_PATTERNS = [
    # AWS Access Key ID
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),

    # AWS Secret Access Key (40-char base64-like string preceded by common labels)
    (r"(?i)(aws_secret|secret_key|aws_secret_access_key)['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}", "AWS Secret Access Key"),

    # Generic API key assignment patterns
    (r"(?i)(api_key|apikey|api_secret|app_secret|client_secret)['\"]?\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Generic API Key"),

    # GitHub Personal Access Token
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),

    # Slack Bot/App Token
    (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack Token"),

    # Stripe Secret Key
    (r"sk_live_[A-Za-z0-9]{24,}", "Stripe Secret Key"),

    # Private key block headers
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key Block"),

    # Generic long hex strings (32–64 chars) following secret-like labels
    (r"(?i)(password|passwd|secret|token|auth)['\"]?\s*[:=]\s*['\"][A-Fa-f0-9]{32,64}['\"]", "Hardcoded Credential"),

    # Bearer tokens in descriptions
    (r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}", "Bearer Token"),

    # Base64-encoded secrets (heuristic: long base64 string after secret label)
    (r"(?i)(secret|token|key|password)['\"]?\s*[:=]\s*['\"][A-Za-z0-9+/]{32,}={0,2}['\"]", "Base64 Encoded Secret"),
]


# ── Helper: Scan Text for Secret Leakage ─────────────────────────────────────

def scan_for_secrets(text: str) -> list[str]:
    """
    Scans a string for patterns that match real secret values.
    Returns a list of matched secret type labels if any are found.
    """
    matched_types = []
    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, text):
            matched_types.append(label)
    return matched_types


# ── Helper: Collect All Violations ───────────────────────────────────────────

def collect_violations(findings: list[SecurityFinding]) -> list[str]:
    """
    Runs all three behavioural checks against the security findings list and
    returns a list of violation messages. An empty list means all checks passed.
    """
    violations = []

    # ── Check 1: CRITICAL Findings Must Have a Concrete Recommendation ────────

    VAGUE_RECOMMENDATION_PHRASES = [
        "fix this",
        "review this",
        "needs attention",
        "should be fixed",
        "address this",
        "look into this",
        "investigate",
        "unclear",
        "unknown",
        "not sure",
        "needs review",
        "manual review required",
        "see documentation",
    ]

    MIN_RECOMMENDATION_LENGTH = 40

    weak_critical_findings = []
    for finding in findings:
        if finding.severity == "CRITICAL":
            rec_lower = finding.recommendation.strip().lower()
            is_too_short = len(rec_lower) < MIN_RECOMMENDATION_LENGTH
            is_vague = any(phrase in rec_lower for phrase in VAGUE_RECOMMENDATION_PHRASES)

            if is_too_short or is_vague:
                weak_critical_findings.append(finding.file_path)

    if weak_critical_findings:
        violations.append(
            f"Check 1 FAILED — {len(weak_critical_findings)} CRITICAL finding(s) "
            f"have vague or insufficiently detailed recommendations: "
            f"{', '.join(weak_critical_findings)}. "
            f"Every CRITICAL finding must include a specific, actionable fix "
            f"of at least {MIN_RECOMMENDATION_LENGTH} characters."
        )

    # ── Check 2: Zero Findings on a Non-Trivial Codebase ─────────────────────
    # NOTE: This check does NOT trigger a hard tripwire — it informs rather
    # than blocks, since an empty result could genuinely mean clean code.

    if len(findings) == 0:
        violations.append(
            "Check 2 ADVISORY — Security Audit Agent returned zero findings. "
            "This may be correct for a small or clean codebase, but if the "
            "codebase is non-trivial, this warrants a manual spot-check. "
            "Consider re-running the Security Audit Agent with a stricter prompt "
            "or reviewing high-risk files manually."
        )

    # ── Check 3: No Secret Values Leaked into Finding Text ───────────────────
    leaked_secrets = []
    for finding in findings:
        combined_text = f"{finding.description} {finding.recommendation}"
        matched_types = scan_for_secrets(combined_text)
        if matched_types:
            leaked_secrets.append(
                f"{finding.file_path} (detected: {', '.join(matched_types)})"
            )

    if leaked_secrets:
        violations.append(
            f"Check 3 FAILED — Actual secret values detected in the text of "
            f"{len(leaked_secrets)} finding(s): {', '.join(leaked_secrets)}. "
            f"The agent must NEVER reproduce actual secret values in descriptions "
            f"or recommendations. Reference the location only (file and line number) "
            f"and instruct the developer to inspect the file directly."
        )

    return violations


# ── Output Guardrail ──────────────────────────────────────────────────────────

@output_guardrail
async def security_audit_guardrail(
    ctx: RunContextWrapper, agent: Agent, output: SecurityAuditOutput
) -> GuardrailFunctionOutput:
    """
    Output guardrail for the Security Audit Agent.

    Runs three behavioural checks on the agent's findings:
      1. CRITICAL findings must have a concrete, actionable recommendation.
      2. Zero findings on a non-trivial codebase triggers a soft advisory.
      3. No actual secret values may appear in finding descriptions or recommendations.

    Check 1 and Check 3 are hard tripwires — they halt the pipeline.
    Check 2 is a soft advisory — it logs a warning but allows the pipeline
    to continue, since an empty result may genuinely mean a clean codebase.
    """

    violations = collect_violations(output.security_findings)

    # Separate hard failures from soft advisories
    hard_failures = [v for v in violations if "FAILED" in v]
    advisories = [v for v in violations if "ADVISORY" in v]

    passed = len(hard_failures) == 0

    if passed and not advisories:
        reason = (
            f"All checks passed. {len(output.security_findings)} finding(s) reviewed — "
            f"CRITICAL recommendations are substantive, no secret leakage detected, "
            f"and finding volume is plausible."
        )
    elif passed and advisories:
        # Soft advisory: pipeline continues but Orchestrator is informed
        reason = (
            f"Checks passed with {len(advisories)} advisory notice(s):\n" +
            "\n".join(f"  - {a}" for a in advisories)
        )
    else:
        # Hard failure: tripwire triggered
        failure_summary = (
            f"{len(hard_failures)} hard check(s) failed"
            + (f" and {len(advisories)} advisory notice(s)" if advisories else "")
            + ":\n"
        )
        all_issues = hard_failures + advisories
        reason = failure_summary + "\n".join(f"  - {i}" for i in all_issues)

    return GuardrailFunctionOutput(
        output_info=SecurityGuardrailResult(passed=passed, reason=reason),
        tripwire_triggered=not passed
    )
