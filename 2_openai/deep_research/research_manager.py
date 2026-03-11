"""Coordinates deep research: guardrails, clarifying questions, then agentic manager (tools + handoffs) with streaming."""
from agents import Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent
from manager_agent import manager_agent
from guardrails import run_guardrails, GuardrailResult


class ResearchManager:
    """Orchestrates clarifying questions and the agentic research manager."""

    async def get_clarifying_questions(self, query: str) -> list[str]:
        """Generate exactly 3 clarifying questions for the query (OpenAI-style first step)."""
        result = await Runner.run(clarifier_agent, f"Query: {query}")
        return result.final_output.questions

    def refine_query_with_answers(
        self,
        query: str,
        questions: list[str],
        answers: list[str],
        recipient_email: str | None = None,
    ) -> str:
        """Combine original query with Q&A and optional recipient email for a refined context."""
        parts = [query]
        if questions and answers:
            qa = []
            for q, a in zip(questions, answers or []):
                a = (a or "").strip()
                if a:
                    qa.append(f"Q: {q}\nA: {a}")
            if qa:
                parts.append("Clarifications:\n" + "\n\n".join(qa))
        if recipient_email and str(recipient_email).strip():
            parts.append("Recipient email: " + str(recipient_email).strip())
        return "\n\n".join(parts)

    def _intent_query_from_refined(self, refined_query: str) -> str:
        """Extract the topic part for intent check (before Clarifications / Recipient email)."""
        q = (refined_query or "").split("Clarifications:")[0].split("Recipient email:")[0].strip()
        return q

    async def run(self, refined_query: str, skip_guardrails: bool = False):
        """Run the agentic manager on the (refined) query; yields status updates and final report.
        Runs input guardrails first unless skip_guardrails=True."""
        if not skip_guardrails:
            intent_query = self._intent_query_from_refined(refined_query)
            gr = run_guardrails(
                refined_query,
                answers=[],
                intent_query=intent_query,
                check_pii=True,
                check_intent=True,
                check_length=True,
                allow_recipient_email=True,
            )
            if not gr.passed:
                yield f"**Input guardrail:** {gr.message}"
                return

        trace_id = gen_trace_id()
        with trace("Deep research trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n\n"
            yield "Starting autonomous research (plan → search → write → evaluate → optimize → email)...\n\n"
            report_snapshot = ""
            result = Runner.run_streamed(manager_agent, refined_query)
            async for event in result.stream_events():
                if event.type == "agent_updated_stream_event":
                    yield f"**{event.new_agent.name}** is working…\n"
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        name = getattr(event.item.raw_item, "name", None) or "tool"
                        yield f"Calling: **{name}**\n"
                    elif event.item.type == "tool_call_output_item":
                        out = getattr(event.item, "output", None)
                        if out:
                            if isinstance(out, str) and ("#" in out or "**" in out) and len(out) > 200:
                                report_snapshot = out
                            elif isinstance(out, dict):
                                report_snapshot = (
                                    out.get("improved_markdown_report")
                                    or out.get("markdown_report")
                                    or report_snapshot
                                )
                        yield "Tool completed.\n"
            try:
                final = result.final_output
                if isinstance(final, str) and len(final) > 100:
                    report_snapshot = final
            except Exception:
                pass
            if report_snapshot:
                yield "\n---\n\n# Report\n\n" + report_snapshot
            else:
                yield "\nResearch run finished. Check trace for full output.\n"
