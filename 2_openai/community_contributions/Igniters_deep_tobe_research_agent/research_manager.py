import json
from typing import AsyncIterator

from agents import Agent, ModelSettings, Runner, function_tool
from agents.stream_events import AgentUpdatedStreamEvent, RunItemStreamEvent

from clarifier_agent import clarifier_agent
from evaluator_agent import evaluator_agent
from llm import large_model
from planner_agent import planner_agent
from schemas import (
    ClarifyingQuestions,
    CoverageAssessment,
    ReportData,
    SearchEvidence,
    WebSearchPlan,
)
from search_agent import search_agent
from writer_agent import writer_agent

MAX_RESEARCH_ROUNDS = 3
MAX_AGENT_TURNS = 40


async def _dump_agent_output(result) -> str:
    final_output = result.final_output
    if hasattr(final_output, "model_dump_json"):
        return final_output.model_dump_json(indent=2)
    return json.dumps(final_output, indent=2, ensure_ascii=False)


@function_tool(
    description_override="Create the next round's structured web-search plan from the current research context.",
    use_docstring_info=False,
)
async def plan_searches(research_context: str) -> str:
    result = await Runner.run(planner_agent, research_context)
    return await _dump_agent_output(result)


@function_tool(
    description_override="Execute one focused research search and return a compact evidence summary with sources.",
    use_docstring_info=False,
)
async def execute_search(search_request: str) -> str:
    result = await Runner.run(search_agent, search_request)
    return await _dump_agent_output(result)


@function_tool(
    description_override="Evaluate whether the gathered evidence is complete enough for the final report.",
    use_docstring_info=False,
)
async def evaluate_coverage(research_context: str) -> str:
    result = await Runner.run(evaluator_agent, research_context)
    return await _dump_agent_output(result)


MANAGER_INSTRUCTIONS = f"""You are the manager agent for a deep research workflow.

You receive the original query, 3 clarifying questions with answers, and the enriched query.
Your job is to autonomously manage the full research process before handing off the final context to
WriterAgent.

Available tools:
- `plan_searches`: use this before every round to create the next structured plan.
- `execute_search`: use this once per planned search item to gather evidence.
- `evaluate_coverage`: use this after each round to assess whether research is sufficient.

Available handoff:
- WriterAgent: use this only after coverage is sufficient or once you have completed
  {MAX_RESEARCH_ROUNDS} rounds.

Workflow:
1. Start at round 1.
2. Call `plan_searches` with the enriched query, round number, existing evidence, and any gaps.
3. Call `execute_search` once per search item. Use parallel tool calls when useful.
4. After each round, call `evaluate_coverage` with all accumulated evidence.
5. If the evaluator says coverage is incomplete and you have completed fewer than
   {MAX_RESEARCH_ROUNDS} rounds, do another targeted round focused only on the gaps.
6. If coverage is sufficient, or you reach {MAX_RESEARCH_ROUNDS} rounds, hand off to WriterAgent.

Rules:
- Never exceed {MAX_RESEARCH_ROUNDS} research rounds.
- Do not ask the user more questions.
- Do not write the final report yourself.
- Keep evidence grouped by round in the context you pass forward.
- When handing off, include the original query, clarifying Q&A, enriched query, all round-by-round
  evidence, and the final coverage assessment."""

research_manager_agent = Agent(
    name="ResearchManager",
    instructions=MANAGER_INSTRUCTIONS,
    model=large_model,
    model_settings=ModelSettings(temperature=0.1, parallel_tool_calls=True),
    tools=[plan_searches, execute_search, evaluate_coverage],
    handoffs=[writer_agent],
)


class ResearchManager:
    async def get_clarifying_questions(self, query: str) -> list[str]:
        result = await Runner.run(clarifier_agent, f"Research query:\n{query}")
        output = result.final_output_as(ClarifyingQuestions)
        return output.questions

    def build_enriched_query(self, query: str, qa_pairs: list[tuple[str, str]]) -> str:
        clarifications = "\n".join(
            f"Q{i + 1}: {question}\nA{i + 1}: {answer}"
            for i, (question, answer) in enumerate(qa_pairs)
        )
        return f"{query}\n\nClarifying Q&A:\n{clarifications}"

    def _build_manager_input(self, query: str, qa_pairs: list[tuple[str, str]]) -> str:
        clarification_block = "\n\n".join(
            f"Q{i + 1}: {question}\nA{i + 1}: {answer}"
            for i, (question, answer) in enumerate(qa_pairs)
        )
        enriched_query = self.build_enriched_query(query, qa_pairs)
        return (
            f"Original query:\n{query}\n\n"
            f"Clarifying Q&A:\n{clarification_block}\n\n"
            f"Enriched query:\n{enriched_query}\n\n"
            f"Maximum research rounds: {MAX_RESEARCH_ROUNDS}"
        )

    def _event_status(self, event, search_counter: int) -> tuple[str | None, int]:
        if isinstance(event, RunItemStreamEvent) and event.name == "tool_called":
            tool_name = getattr(event.item.raw_item, "name", "")
            if tool_name == "plan_searches":
                return "Manager is planning the next research round...", search_counter
            if tool_name == "execute_search":
                search_counter += 1
                return f"Manager is executing search {search_counter}...", search_counter
            if tool_name == "evaluate_coverage":
                return "Manager is evaluating research coverage...", search_counter

        if isinstance(event, AgentUpdatedStreamEvent) and event.new_agent.name == writer_agent.name:
            return "Writer agent is drafting the final report...", search_counter

        if isinstance(event, RunItemStreamEvent) and event.name == "handoff_occured":
            target_agent = getattr(event.item, "target_agent", None)
            if target_agent and target_agent.name == writer_agent.name:
                return "Writer agent is drafting the final report...", search_counter

        return None, search_counter

    async def run_research(
        self,
        query: str,
        qa_pairs: list[tuple[str, str]],
    ) -> AsyncIterator[tuple[str, str]]:
        manager_input = self._build_manager_input(query, qa_pairs)
        search_counter = 0
        latest_report = ""

        yield "Starting deep research with the enriched query...", latest_report

        stream = Runner.run_streamed(
            research_manager_agent,
            manager_input,
            max_turns=MAX_AGENT_TURNS,
        )

        async for event in stream.stream_events():
            status_text, search_counter = self._event_status(event, search_counter)
            if status_text:
                yield status_text, latest_report

        report = stream.final_output_as(ReportData, raise_if_incorrect_type=True)
        latest_report = report.markdown_report
        yield "Research complete.", latest_report
