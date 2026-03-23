from typing import Iterable

from agents import Runner, gen_trace_id, trace

from clarifier_agent import ClarificationQuestions, clarifier_agent
from config import (
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_EVALUATION_TARGET,
    DEFAULT_OUTPUT_FORMAT,
)
from manager_agent import manager_agent


class ResearchManager:
    async def get_clarifying_questions(self, query: str) -> ClarificationQuestions:
        result = await Runner.run(clarifier_agent, f"Query: {query}")
        return result.final_output_as(ClarificationQuestions)

    async def run(self, query: str, answers: Iterable[str]):
        """
        Execute end-to-end orchestration:
        clarifier -> manager(tools + handoffs) -> final report markdown.
        """
        trace_id = gen_trace_id()
        with trace("MideSeniorDev Deep Research Trace", trace_id=trace_id):
            yield f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Collecting clarification context..."

            formatted_input = self._build_manager_input(query, answers)
            yield "Running manager orchestration (tools + handoffs)..."

            result = await Runner.run(manager_agent, formatted_input)
            yield "Research complete."
            yield str(result.final_output)

    def _build_manager_input(self, query: str, answers: Iterable[str]) -> str:
        answer_list = [a.strip() for a in answers]
        safe_answers = [
            answer_list[0] if len(answer_list) > 0 and answer_list[0] else DEFAULT_OUTPUT_FORMAT,
            answer_list[1] if len(answer_list) > 1 and answer_list[1] else DEFAULT_ALLOWED_TOOLS,
            answer_list[2] if len(answer_list) > 2 and answer_list[2] else DEFAULT_EVALUATION_TARGET,
        ]
        return (
            f"Original query: {query}\n\n"
            "Clarification answers:\n"
            f"1) Deliverable/citations: {safe_answers[0]}\n"
            f"2) Allowed tools/providers: {safe_answers[1]}\n"
            f"3) Evaluation/demo expectations: {safe_answers[2]}\n"
        )
