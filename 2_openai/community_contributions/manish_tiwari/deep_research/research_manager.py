import asyncio

from pydantic import BaseModel, Field

from agents import Agent, Runner, function_tool, gen_trace_id, handoff, trace
from agents.extensions import handoff_filters

from email_agent import email_agent
from evaluator_agent import EvaluationResult, evaluator_agent
from planner_agent import (
    ClarifyingQuestions,
    WebSearchPlan,
    clarifying_planner_agent,
    planner_agent,
)
from search_agent import search_agent
from writer_agent import ReportData, writer_agent

MAX_RESEARCH_ITERATIONS = 5
EVAL_PASS_THRESHOLD = 7

RECOMMENDED_PROMPT_PREFIX = (
    "# System context\nYou are part of a multi-agent system (Agents SDK). "
    "Agents can use **tools** and **handoffs**. Handoffs use functions like `transfer_to_<agent_name>`. "
    "Do not narrate internal transfers to the end user.\n"
)

MANAGER_INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    "You are the Research Manager for one iteration of a deep-research job.\n"
    "Tools:\n"
    "- `run_planner`: Pass a rich planning_context string (query, clarifications, prior evaluator JSON, "
    "optional notes on what to avoid duplicating). Returns a JSON search plan.\n"
    "- `run_search_item`: For each plan item, call with that item's query and reason.\n"
    "- `run_writer`: After searches, call with no args to build the structured report from accumulated snippets.\n"
    "- `run_evaluator`: Call with the latest markdown report string.\n"
    "Standard flow: run_planner → one run_search_item per planned query → run_writer → run_evaluator.\n"
    f"When evaluator score ≥ {EVAL_PASS_THRESHOLD} and should_continue_research is false, "
    "hand off to the email agent and include the full markdown report in your transfer message.\n"
    "Always finish with structured output `ManagerIterationResult` (latest_evaluator_score from the evaluator tool, "
    "needs_more_search aligned with should_continue_research, stop_research when done or when handing off email)."
)


class ManagerIterationResult(BaseModel):
    iteration_notes: str = Field(description="Brief status for logging.")
    latest_evaluator_score: int = Field(
        ge=0,
        le=10,
        description="Last evaluator score; 0 if not run.",
    )
    needs_more_search: bool = Field(
        description="True if another outer research iteration should run.",
    )
    stop_research: bool = Field(description="True if the outer loop should stop after this round.")


email_handoff = handoff(
    agent=email_agent,
    tool_description_override="Send the finalized research report by email (HTML).",
    input_filter=handoff_filters.remove_all_tools,
)


def _normalize_three_questions(raw: list[str]) -> list[str]:
    cleaned = [q.strip() for q in raw if q and str(q).strip()]
    out = cleaned[:3]
    while len(out) < 3:
        out.append("Any other constraints or preferences for this research?")
    return out


class ResearchManager:
    async def run(self, query: str, clarification_answers: str | None = None):
        """Clarifying questions first; then autonomous manager iterations with evaluator-driven replanning."""
        trace_id = gen_trace_id()
        trace_line = f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
        with trace("Research trace", trace_id=trace_id):
            answers = (clarification_answers or "").strip()
            if not answers:
                try:
                    cq = await Runner.run(
                        clarifying_planner_agent,
                        f"Research query:\n{(query or '').strip() or '(empty — ask generic scoping questions)'}",
                    )
                    parsed = cq.final_output_as(ClarifyingQuestions)
                    qs = _normalize_three_questions(parsed.questions)
                except Exception as exc:
                    yield (
                        f"{trace_line}\n\n"
                        "### Clarifying questions\n\n"
                        f"_Could not generate questions ({exc!s}). Please add details in “Clarification answers” "
                        "and run again, or retry._"
                    )
                    return

                body = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(qs))
                # Single yield so Gradio’s streaming output is not overwritten by an earlier chunk.
                yield (
                    f"{trace_line}\n\n"
                    "### Clarifying questions\n\n"
                    f"{body}\n\n"
                    "---\n\n"
                    "**Answer these in the “Clarification answers” field**, then click **Run** again."
                )
                return

            ctx: dict = {
                "query": query,
                "clarifications": answers,
                "last_plan": None,
                "search_results": [],
                "last_report": None,
                "last_eval_json": None,
            }

            yield (
                f"{trace_line}\n\n"
                "Starting autonomous research (manager agent with specialist tools)…"
            )

            for round_i in range(1, MAX_RESEARCH_ITERATIONS + 1):
                yield f"Research iteration {round_i}/{MAX_RESEARCH_ITERATIONS}…"

                @function_tool
                async def run_planner_tool(planning_context: str) -> str:
                    """Create or refine a WebSearchPlan."""
                    result = await Runner.run(planner_agent, planning_context)
                    plan = result.final_output_as(WebSearchPlan)
                    ctx["last_plan"] = plan
                    return plan.model_dump_json()

                @function_tool
                async def run_search_item_tool(search_term: str, reason: str) -> str:
                    """Run one web search; results accumulate for the writer."""
                    block = (
                        f"Original research query:\n{ctx['query']}\n\n"
                        f"Clarifying questions and user answers:\n{ctx['clarifications']}\n\n"
                        f"Search term: {search_term}\nReason for searching: {reason}"
                    )
                    result = await Runner.run(search_agent, block)
                    out = str(result.final_output)
                    ctx["search_results"].append(f"---\nTerm: {search_term}\n{out}")
                    return out

                @function_tool
                async def run_searches_from_plan_tool() -> str:
                    """Execute all items in the last plan in parallel (same inputs as single-search tool)."""
                    plan: WebSearchPlan | None = ctx.get("last_plan")
                    if not plan or not plan.searches:
                        return "No plan available; call run_planner first."

                    async def one(item):
                        block = (
                            f"Original research query:\n{ctx['query']}\n\n"
                            f"Clarifying questions and user answers:\n{ctx['clarifications']}\n\n"
                            f"Search term: {item.query}\nReason for searching: {item.reason}"
                        )
                        try:
                            result = await Runner.run(search_agent, block)
                            out = str(result.final_output)
                            ctx["search_results"].append(f"---\nTerm: {item.query}\n{out}")
                            return f"OK: {item.query}"
                        except Exception as exc:
                            return f"Failed: {item.query} ({exc})"

                    results = await asyncio.gather(*[one(s) for s in plan.searches])
                    return "\n".join(results)

                @function_tool
                async def run_writer_tool() -> str:
                    """Synthesize accumulated search snippets into the structured report."""
                    bundle = "\n\n".join(ctx["search_results"]) if ctx["search_results"] else "(no search results yet)"
                    writer_input = (
                        f"Original query:\n{ctx['query']}\n\n"
                        f"Clarifications (Q&A):\n{ctx['clarifications']}\n\n"
                        f"Summarized search results:\n{bundle}"
                    )
                    result = await Runner.run(writer_agent, writer_input)
                    report = result.final_output_as(ReportData)
                    ctx["last_report"] = report
                    return report.markdown_report

                @function_tool
                async def run_evaluator_tool(report_markdown: str) -> str:
                    """Score the report; JSON is stored for the next iteration's planner."""
                    ev_input = (
                        f"Original query:\n{ctx['query']}\n\n"
                        f"User clarifications:\n{ctx['clarifications']}\n\n"
                        f"Report to evaluate (markdown):\n{report_markdown}"
                    )
                    result = await Runner.run(evaluator_agent, ev_input)
                    ev = result.final_output_as(EvaluationResult)
                    ctx["last_eval_json"] = ev.model_dump_json()
                    return ctx["last_eval_json"]

                refinement = ctx["last_eval_json"] or "None yet (first iteration)."
                user_msg = (
                    f"--- Research iteration {round_i} of {MAX_RESEARCH_ITERATIONS} ---\n"
                    f"Original query:\n{query}\n\n"
                    f"User clarifications (answers):\n{answers}\n\n"
                    f"Prior evaluator JSON:\n{refinement}\n\n"
                    f"Accumulated search snippets: {len(ctx['search_results'])}.\n\n"
                    "For run_planner, pass a single planning_context string that includes the query, clarifications, "
                    "the prior evaluator JSON, and instructions to avoid duplicate themes when refining.\n"
                    "Prefer run_searches_from_plan_tool after planning to run all planned searches in one step, "
                    "unless a subset is explicitly needed.\n"
                    "Then run_writer_tool, run_evaluator_tool with that markdown.\n"
                    f"If score ≥ {EVAL_PASS_THRESHOLD} and should_continue_research is false, "
                    "hand off to email with the full markdown report.\n"
                    "End with ManagerIterationResult."
                )

                manager_agent = Agent(
                    name="ResearchManagerAgent",
                    instructions=MANAGER_INSTRUCTIONS,
                    model="gpt-4o-mini",
                    tools=[
                        run_planner_tool,
                        run_search_item_tool,
                        run_searches_from_plan_tool,
                        run_writer_tool,
                        run_evaluator_tool,
                    ],
                    handoffs=[email_handoff],
                    output_type=ManagerIterationResult,
                )

                await Runner.run(manager_agent, user_msg, max_turns=45)

                last_score = 0
                needs_more = True
                if ctx["last_eval_json"]:
                    ev = EvaluationResult.model_validate_json(ctx["last_eval_json"])
                    last_score = ev.score
                    needs_more = ev.should_continue_research

                yield (
                    f"Round {round_i}: evaluator score={last_score}, "
                    f"should_continue_research={needs_more}, snippets={len(ctx['search_results'])}"
                )

                if last_score >= EVAL_PASS_THRESHOLD and not needs_more:
                    break

            report = ctx.get("last_report")
            if report is None:
                yield "Research ended without a report."
                return

            yield "### Final report\n\n" + report.markdown_report

            yield "Sending email…"
            try:
                await Runner.run(email_agent, report.markdown_report)
                yield "Email step completed."
            except Exception as exc:
                yield f"Email step failed: {exc}"
