"""Prompt builders for each LLM node in the 5 Whys agent."""

from __future__ import annotations

from datetime import datetime


def _tree_summary(nodes: list[dict]) -> str:
    if not nodes:
        return "(none yet — this is the first level)"
    lines = []
    for n in nodes:
        status = "OK (ruled out)" if n["gemba_result"] == "OK" else "NOK (confirmed)"
        line = f"  [{n['branch_path']}] depth={n['depth']} | {status} | {n['hypothesis']}"
        if n.get("gemba_notes"):
            line += f"\n    Operator notes: {n['gemba_notes']}"
        if n.get("countermeasure"):
            line += f"\n    Countermeasure: {n['countermeasure']}"
        lines.append(line)
    return "\n".join(lines)


def why_prompts(
    domain: str,
    equipment_context: str,
    phenomenon: str,
    depth: int,
    branch_path: str,
    nodes: list[dict],
    domain_context: str,
    current_problem: str,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the why_generator node."""
    system = (
        f"You are an expert root cause analyst specialising in {domain}.\n"
        f"Today is {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n"
        f"Equipment / process context: {equipment_context or 'not specified'}.\n\n"
        "Your task: use search and Wikipedia tools to research known failure modes, "
        "then propose 1–5 specific, testable hypotheses for WHY the given problem occurs.\n"
        "Be concrete — each hypothesis must describe a physical or process mechanism "
        "an operator can verify with a Gemba Check.\n"
        "Do NOT re-propose any cause that already appears in the investigation history.\n"
        "For each cause, provide DISTINCT gemba instructions specific to verifying that "
        "cause only. Do NOT reuse the same instructions across different causes.\n"
        "After your research, respond with the structured output schema."
    )
    user = (
        f"Original phenomenon: '{phenomenon}'\n\n"
        f"Investigation history so far:\n{_tree_summary(nodes)}\n\n"
        f"Problem to drill into now (depth {depth}, branch {branch_path}):\n"
        f"'{current_problem}'\n\n"
        f"Domain context: {domain_context}\n\n"
        "Propose new hypotheses not yet investigated. Use tools as needed, "
        "then provide your structured hypothesis output."
    )
    return system, user


def validator_prompts(
    domain: str,
    phenomenon: str,
    depth: int,
    max_depth: int,
    active: dict,
    nodes: list[dict],
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the root_cause_validator node."""
    tree = "\n".join(
        f"  [{n['branch_path']}] depth={n['depth']} | {n['gemba_result']} | {n['hypothesis']}"
        for n in nodes
    )
    system = (
        f"You are a senior root cause analyst for {domain}.\n"
        "Evaluate whether the confirmed cause is a TRUE ROOT CAUSE or an intermediate symptom.\n"
        "A root cause is one where fixing it prevents the original phenomenon from recurring.\n\n"
        "CRITICAL RULE: Human error, operator mistake, or any cause that blames a person's "
        "behaviour is NEVER a root cause. Human behaviour is always a symptom of a deeper "
        "systemic, process, or design failure (e.g. missing procedure, inadequate training, "
        "poor equipment design, absent error-proofing). If the confirmed cause describes "
        "human action or inaction, set is_root_cause=False and direct the probe toward the "
        "underlying system or process that enabled or failed to prevent that behaviour."
    )
    user = (
        f"Original phenomenon: '{phenomenon}'\n\n"
        f"Current depth: {depth} of {max_depth}\n\n"
        f"Confirmed cause (Gemba NOK):\n  '{active.get('hypothesis', '')}'\n"
        f"Operator notes: '{active.get('gemba_notes', '')}'\n\n"
        f"Investigation tree so far:\n{tree or '  (none yet)'}\n\n"
        "Is this a root cause or an intermediate symptom? Provide your structured decision."
    )
    return system, user


def countermeasure_prompts(
    domain: str,
    phenomenon: str,
    active: dict,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the countermeasure_generator node."""
    system = (
        f"You are an operational excellence expert in {domain}.\n"
        "Propose a specific, actionable countermeasure to eliminate the confirmed root cause "
        "and prevent recurrence of the original phenomenon."
    )
    user = (
        f"Original phenomenon: '{phenomenon}'\n"
        f"Confirmed root cause: '{active.get('hypothesis', '')}'\n"
        f"Operator notes: '{active.get('gemba_notes', '')}'\n"
        f"Validator reasoning: '{active.get('validator_reasoning', '')}'\n\n"
        "Provide your structured countermeasure."
    )
    return system, user
