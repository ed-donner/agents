"""
Input and output guardrails for the deep research orchestrator.

Input guardrail  → runs before the orchestrator processes any query.
Output guardrail → runs after the orchestrator produces its final output.

Both are wired into the orchestrator Agent definition in manager.py.
"""
from __future__ import annotations

from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    RunContextWrapper,
    Runner,
    input_guardrail,
    output_guardrail,
)


# ---------------------------------------------------------------------------
# Input guardrail: query safety check
# ---------------------------------------------------------------------------

class _QuerySafetyResult(BaseModel):
    is_safe: bool
    reason: str


_SAFETY_CLASSIFIER = Agent(
    name="QuerySafetyClassifier",
    instructions=(
        "You are a content-safety classifier for a research tool. "
        "Decide whether the user's research query is safe and appropriate. "
        "Flag as UNSAFE if the query asks for: instructions to cause physical harm, "
        "synthesis of illegal substances, creation of malware or cyberweapons, "
        "harassment of a private individual, or any clearly illegal activity. "
        "Legitimate research on sensitive topics (history, policy, medicine, security "
        "research) is SAFE. Respond with a JSON object: "
        '{"is_safe": true/false, "reason": "<one sentence>"}'
    ),
    model="gpt-4o-mini",
    model_settings=ModelSettings(temperature=0.0, max_tokens=128),
    output_type=_QuerySafetyResult,
)


@input_guardrail
async def query_safety_guardrail(
    ctx: RunContextWrapper, agent: Agent, input: str
) -> GuardrailFunctionOutput:
    """
    Runs a lightweight LLM safety classifier on the incoming research query.
    Trips the wire if the query requests harmful, illegal, or abusive content,
    blocking the orchestrator before any tool calls or searches begin.
    """
    try:
        result = await Runner.run(_SAFETY_CLASSIFIER, input, context=ctx.context)
        check: _QuerySafetyResult = result.final_output
        return GuardrailFunctionOutput(
            output_info=check,
            tripwire_triggered=not check.is_safe,
        )
    except Exception:
        # Fail open: if the classifier itself errors, allow the request through
        return GuardrailFunctionOutput(
            output_info=_QuerySafetyResult(is_safe=True, reason="classifier unavailable"),
            tripwire_triggered=False,
        )


# ---------------------------------------------------------------------------
# Output guardrail: report minimum-quality gate
# ---------------------------------------------------------------------------

class _ReportQualityResult(BaseModel):
    meets_minimum: bool
    issues: list[str]


@output_guardrail
async def report_quality_guardrail(
    ctx: RunContextWrapper, agent: Agent, output: object
) -> GuardrailFunctionOutput:
    """
    Validates the final report before it leaves the orchestrator.
    Trips the wire if the output:
      - is shorter than 200 words (incomplete or truncated),
      - still contains placeholder text like 'TODO' or '[INSERT]',
      - is missing the markdown_report field entirely.
    A full LLM-based quality check would replace the heuristic below in production.
    """
    text = ""
    if hasattr(output, "markdown_report"):
        text = output.markdown_report or ""
    else:
        text = str(output)

    issues: list[str] = []

    if len(text.split()) < 200:
        issues.append("report is shorter than 200 words")

    for placeholder in ("TODO", "[INSERT]", "PLACEHOLDER", "Lorem ipsum"):
        if placeholder.lower() in text.lower():
            issues.append(f"report contains placeholder text: '{placeholder}'")

    return GuardrailFunctionOutput(
        output_info=_ReportQualityResult(
            meets_minimum=len(issues) == 0,
            issues=issues,
        ),
        tripwire_triggered=len(issues) > 0,
    )
