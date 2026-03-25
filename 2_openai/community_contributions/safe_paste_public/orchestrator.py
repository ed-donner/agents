"""Orchestrates scanner → redaction coach OR explainer (same pattern as 2_openai/deep_research)."""

from agents import InputGuardrailTripwireTriggered, Runner, gen_trace_id, trace

from explainer_agent import explainer_agent
from models import ExplainerResult, RiskLevel, ScanResult
from redaction_coach_agent import redaction_coach_agent
from scanner_agent import scanner_agent


def _format_explainer(r: ExplainerResult) -> str:
    causes = "\n".join(f"- {c}" for c in r.likely_causes)
    steps = "\n".join(f"- {s}" for s in r.next_steps)
    tail = f"\n\n**Cautions:** {r.cautions}" if r.cautions.strip() else ""
    return (
        f"## Summary\n{r.summary}\n\n"
        f"## Likely causes\n{causes}\n\n"
        f"## Next steps\n{steps}{tail}"
    )


class SafePasteManager:
    """Multi-agent flow: scan → (redact) or (explain with input guardrail)."""

    async def run(self, text: str):
        trace_id = gen_trace_id()
        with trace("Safe paste check", trace_id=trace_id):
            yield (
                f"**Trace:** https://platform.openai.com/traces/trace?trace_id={trace_id}\n\n"
                "---\n"
            )
            yield "**Status:** Scanning paste…\n\n"
            scan = await Runner.run(
                scanner_agent,
                f"Analyze this text for public-posting risk:\n\n{text}",
            )
            scan_result = scan.final_output_as(ScanResult)

            yield (
                f"**Scanner:** risk=`{scan_result.risk_level.value}` — "
                f"{scan_result.summary}\n\n---\n\n"
            )

            if scan_result.risk_level in (RiskLevel.high, RiskLevel.critical):
                yield "**Status:** High risk — redaction guidance only (explainer skipped).\n\n"
                coach_prompt = (
                    f"Scanner summary: {scan_result.summary}\n"
                    f"Categories: {', '.join(scan_result.categories)}\n"
                    f"Notes: {scan_result.notes_for_orchestrator}\n\n"
                    f"Original paste:\n{text}"
                )
                coach = await Runner.run(redaction_coach_agent, coach_prompt)
                yield str(coach.final_output)
                return

            # low / medium — try explainer (input guardrail on explainer is second line of defense)
            yield "**Status:** Explaining error/log…\n\n"
            warn = ""
            if scan_result.risk_level == RiskLevel.medium:
                warn = (
                    "Scanner flagged **medium** risk (e.g. possible PII). "
                    "Do not repeat personal identifiers in your answer.\n\n"
                )
            explainer_prompt = f"{warn}Paste to explain:\n\n{text}"

            try:
                result = await Runner.run(explainer_agent, explainer_prompt)
                expl = result.final_output_as(ExplainerResult)
                yield _format_explainer(expl)
            except InputGuardrailTripwireTriggered:
                yield (
                    "**Guardrail blocked explanation** — the paste still looks like it contains "
                    "secrets or tokens. Remove or replace those values, then try again.\n\n"
                    "**Status:** Generating redaction guidance instead…\n\n"
                )
                coach_prompt = (
                    f"Scanner summary: {scan_result.summary}\n"
                    f"Categories: {', '.join(scan_result.categories)}\n"
                    f"The explainer guardrail refused to run — treat as sensitive.\n\n"
                    f"Original paste:\n{text}"
                )
                coach = await Runner.run(redaction_coach_agent, coach_prompt)
                yield str(coach.final_output)
