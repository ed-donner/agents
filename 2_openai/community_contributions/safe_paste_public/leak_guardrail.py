"""Second-line input guardrail before the explainer runs (regex fast path + tiny classifier)."""

import re

from agents import Agent, GuardrailFunctionOutput, Runner, input_guardrail

from models import LeakPrecheckOutput


def _regex_looks_sensitive(text: str) -> bool:
    """Cheap heuristics — catches obvious cases without an LLM call."""
    if not text or not isinstance(text, str):
        return False
    patterns = (
        r"(?i)bearer\s+[a-z0-9._\-]{15,}",
        r"(?i)(authorization|api[_-]?key|secret|password|token)\s*[:=]\s*\S+",
        r"(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        r"\bsk-[a-zA-Z0-9]{10,}",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"(?i)xox[baprs]-[0-9a-z-]+",
    )
    return any(re.search(p, text) for p in patterns)


_PRECHECK_INSTRUCTIONS = """
Decide if the user message still contains sensitive material that must not be explained or amplified:
API keys, bearer tokens, passwords in URLs, private keys, long random secrets in headers.

Return contains_sensitive=true if ANY of those appear to be present.
Return false only for stack traces and logs that look scrubbed or generic.

In reason, explain briefly without quoting secret substrings.
"""

leak_precheck_agent = Agent(
    name="LeakPrecheckAgent",
    instructions=_PRECHECK_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=LeakPrecheckOutput,
)


def _coerce_text(message) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        return "\n".join(str(x) for x in message)
    return str(message)


@input_guardrail
async def leak_input_guardrail(ctx, agent, message):
    """Blocks the explainer when the paste still looks unsafe."""
    text = _coerce_text(message)
    if _regex_looks_sensitive(text):
        return GuardrailFunctionOutput(
            output_info={"mode": "regex", "blocked": True},
            tripwire_triggered=True,
        )

    result = await Runner.run(leak_precheck_agent, text, context=ctx.context)
    output = result.final_output
    return GuardrailFunctionOutput(
        output_info={"precheck": output.model_dump()},
        tripwire_triggered=output.contains_sensitive,
    )
