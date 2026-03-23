"""
Agentic Research Orchestrator
==============================
This module converts the original Python-script manager into a true Agent.

Key patterns applied from 2_openai labs:
  - Agents-as-tools (lab 3): every specialist worker is exposed via .as_tool()
    so the orchestrator can call them like functions while the LLM decides the
    order and iteration count.
  - Handoffs (lab 2): when the report is approved the orchestrator hands off
    to the email agent -- it never returns to the orchestrator.
  - Guardrails (lab 3): an input safety check wraps the orchestrator.
  - Parallel search: a @function_tool runs all searches concurrently with
    asyncio.gather, matching the parallel-execution pattern from lab 2.
  - Loop / self-correction: the orchestrator's instructions allow up to
    MAX_SEARCH_RETRIES sufficiency checks and MAX_REPORT_RETRIES report
    revisions before accepting the current output.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from agents import Agent, ModelSettings, Runner, function_tool, gen_trace_id, trace
from agents.exceptions import InputGuardrailTripwireTriggered
from config import DEFAULT_MODEL

from research_agents import (
    clarifier_agent,
    email_agent,
    evaluator_agent,
    planner_agent,
    search_agent,
    sufficiency_agent,
    writer_agent,
)
from guardrails import query_safety_guardrail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_SEARCH_RETRIES = 2   # how many extra search rounds the agent may trigger
MAX_REPORT_RETRIES = 1   # how many times the agent may rewrite after bad eval

# ---------------------------------------------------------------------------
# Parallel search executor
# Accepts a JSON-encoded list of query strings and runs them concurrently.
# ---------------------------------------------------------------------------
@function_tool
async def run_parallel_searches(queries_json: str) -> str:
    """
    Execute multiple web searches in parallel.
    Pass a JSON array of search query strings, e.g. '["query1","query2"]'.
    Returns the combined results as a single string, one section per query.
    """
    try:
        queries: list[str] = json.loads(queries_json)
    except json.JSONDecodeError:
        queries = [q.strip() for q in queries_json.split("\n") if q.strip()]

    async def _search_one(query: str) -> str:
        try:
            r = await Runner.run(search_agent, f"Search term: {query}")
            return f"### {query}\n{r.final_output}\n"
        except Exception as exc:
            return f"### {query}\nSearch failed: {exc}\n"

    results = await asyncio.gather(*[_search_one(q) for q in queries[:10]])
    return "\n---\n".join(results)


# ---------------------------------------------------------------------------
# Expose specialist agents as tools (agent-as-tool pattern from lab 3)
# ---------------------------------------------------------------------------
clarify_tool = clarifier_agent.as_tool(
    tool_name="clarify_query",
    tool_description="Generate three clarifying questions to sharpen the research scope.",
)

plan_tool = planner_agent.as_tool(
    tool_name="plan_searches",
    tool_description=(
        "Given the query and user clarifications, produce a prioritised list of "
        "web search queries as a WebSearchPlan JSON."
    ),
)

sufficiency_tool = sufficiency_agent.as_tool(
    tool_name="check_sufficiency",
    tool_description=(
        "Given the query and all search results so far, decide whether the evidence "
        "is sufficient. Returns a ResearchSufficiencyCheck JSON with is_sufficient, "
        "missing_aspects, and additional_queries."
    ),
)

write_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description=(
        "Synthesise the query, clarifications, and all search results into a detailed "
        "Markdown report. Returns a ReportData JSON."
    ),
)

evaluate_tool = evaluator_agent.as_tool(
    tool_name="evaluate_report",
    tool_description=(
        "Score the report 0-10 and decide whether to approve it. Returns a "
        "ReportEvaluation JSON with is_approved, score, and improvement_suggestions."
    ),
)

# ---------------------------------------------------------------------------
# Orchestrator instructions
# ---------------------------------------------------------------------------
_INSTRUCTIONS = f"""
You are a Deep Research Orchestrator. Your job is to coordinate a team of specialist
agents to answer a research query thoroughly and accurately.

You have the following tools available:
  - clarify_query         : generate 3 scoping questions (already answered by user input)
  - plan_searches         : turn the query + clarifications into search terms
  - run_parallel_searches : execute all searches concurrently; pass a JSON array of strings
  - check_sufficiency     : decide if the evidence is enough; may suggest more queries
  - write_report          : synthesise evidence into a full Markdown report
  - evaluate_report       : score the report and approve or request revisions

Follow this workflow but use your judgement to iterate:

STEP 1  Read the input carefully. Extract the original query and any clarifications.
STEP 2  Call plan_searches with the full context.
STEP 3  Call run_parallel_searches with the query strings from the plan (JSON array).
STEP 4  Call check_sufficiency. If not sufficient and retries < {MAX_SEARCH_RETRIES},
        call plan_searches with the missing_aspects, then run_parallel_searches again,
        then re-check. Stop iterating after {MAX_SEARCH_RETRIES} extra rounds.
STEP 5  Call write_report with ALL accumulated search results.
STEP 6  Call evaluate_report. If not approved and retries < {MAX_REPORT_RETRIES},
        revise by calling write_report again, incorporating the improvement_suggestions.
STEP 7  Once the report is approved (or retries exhausted), hand off to the email agent.

At each step, output a brief status line so the user can follow your progress,
e.g. "Planning searches...", "Running searches in parallel...", "Evaluating report...".
Always include the final Markdown report in your last message before the handoff.
"""

# ---------------------------------------------------------------------------
# The orchestrator Agent
# ---------------------------------------------------------------------------
orchestrator = Agent(
    name="ResearchOrchestrator",
    instructions=_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    model_settings=ModelSettings(
        temperature=0.2,
        max_tokens=4096,
        top_p=0.95,
    ),
    tools=[
        clarify_tool,
        plan_tool,
        run_parallel_searches,
        sufficiency_tool,
        write_tool,
        evaluate_tool,
    ],
    handoffs=[email_agent],
    input_guardrails=[query_safety_guardrail],
    # Output guardrail is not on the orchestrator -- the orchestrator's final
    # message is a brief handoff note, not the report itself. The quality check
    # is applied inside ResearchManager.run() on the extracted report text.
)


# ---------------------------------------------------------------------------
# ResearchManager: thin async wrapper that yields status strings for the UI
# ---------------------------------------------------------------------------
class ResearchManager:
    """
    Streams status updates and the final report to the caller.
    The caller iterates over the async generator:

        async for update in ResearchManager().run(query, clarifications):
            print(update)
    """

    async def run(
        self,
        query: str,
        clarifications: str = "",
    ) -> AsyncGenerator[str, None]:
        trace_id = gen_trace_id()
        full_input = self._build_input(query, clarifications)

        with trace("Deep Research", trace_id=trace_id):
            yield "Starting research...\n"

            try:
                stream = Runner.run_streamed(orchestrator, full_input)

                async for event in stream.stream_events():
                    update = self._event_to_status(event)
                    if update:
                        yield update

                final = stream.final_output
                if final:
                    report_text = (
                        final.markdown_report
                        if hasattr(final, "markdown_report")
                        else str(final)
                    )

                    word_count = len(report_text.split())
                    if word_count < 200:
                        yield (
                            f"Warning: Report is too short ({word_count} words). "
                            "The agent may not have called write_report. "
                            "Try running again.\n"
                        )
                    else:
                        yield f"Report ready ({word_count} words).\n"
                        yield "\n---\n" + report_text

            except InputGuardrailTripwireTriggered as exc:
                yield f"Blocked: Query did not pass the safety check -- {exc}\n"
            except Exception as exc:
                yield f"Error during research: {exc}\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_input(query: str, clarifications: str) -> str:
        text = f"Research query: {query}"
        if clarifications.strip():
            text += f"\n\nUser clarifications:\n{clarifications.strip()}"
        return text

    @staticmethod
    def _event_to_status(event) -> str | None:
        """Convert a stream event to a human-readable status line."""
        etype = getattr(event, "type", "")

        if etype == "agent_updated_stream_event":
            return f"Agent: {event.new_agent.name}\n"

        if etype == "run_item_stream_event":
            item = getattr(event, "item", None)
            if item is None:
                return None

            item_type = type(item).__name__

            if "ToolCall" in item_type and "Output" not in item_type:
                raw = getattr(item, "raw_item", {})
                if isinstance(raw, dict):
                    tool_name = raw.get("name") or raw.get("function", {}).get("name", "tool")
                else:
                    tool_name = getattr(raw, "name", None) or getattr(item, "name", "tool")
                return f"Calling: {tool_name}\n"

            if "ToolCall" in item_type and "Output" in item_type:
                raw = getattr(item, "raw_item", {})
                if isinstance(raw, dict):
                    tool_name = raw.get("name", "tool")
                else:
                    tool_name = getattr(item, "name", "tool")
                return f"Done: {tool_name}\n"

            if "Handoff" in item_type:
                return "Handing off to email agent...\n"

        return None
