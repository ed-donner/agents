import asyncio

from agents import Runner, gen_trace_id, trace

from brief_writer_agent import DecisionBrief, brief_writer_agent
from review_agents import Review, review_agents
from research_agents import SearchItem, SearchPlan, planner_agent, search_agent


class BriefManager:
    async def run(self, question: str, context: str):
        trace_id = gen_trace_id()
        with trace("Decision brief workflow", trace_id=trace_id):
            yield "Planning five focused searches for current evidence..."
            search_plan = await self._plan_searches(question, context)

            yield f"Running {len(search_plan.searches)} web searches in parallel..."
            research = await self._run_searches(search_plan)

            yield "Research complete. Starting strategy, risk, and execution reviews..."
            reviews = await self._run_reviews(question, context, research)

            yield "Specialist reviews complete. Synthesizing the decision brief..."
            brief = await self._write_brief(question, context, research, reviews)

            yield brief.to_markdown()

    async def _plan_searches(self, question: str, context: str) -> SearchPlan:
        result = await Runner.run(planner_agent, self._source_prompt(question, context))
        return result.final_output

    async def _run_searches(self, search_plan: SearchPlan) -> list[str]:
        results = await asyncio.gather(
            *(self._search(item) for item in search_plan.searches)
        )
        return results

    async def _search(self, item: SearchItem) -> str:
        prompt = f"Search query: {item.query}\nReason: {item.reason}"
        result = await Runner.run(search_agent, prompt)
        return result.final_output

    async def _run_reviews(
        self, question: str, context: str, research: list[str]
    ) -> list[Review]:
        prompt = self._evidence_prompt(question, context, research)
        results = await asyncio.gather(
            *(Runner.run(agent, prompt) for agent in review_agents)
        )
        return [result.final_output for result in results]

    async def _write_brief(
        self, question: str, context: str, research: list[str], reviews: list[Review]
    ) -> DecisionBrief:
        reviews_json = "\n\n".join(review.model_dump_json(indent=2) for review in reviews)
        prompt = f"""Create the final decision brief.

{self._evidence_prompt(question, context, research)}

SPECIALIST REVIEWS
{reviews_json}
"""
        result = await Runner.run(brief_writer_agent, prompt)
        return result.final_output

    @staticmethod
    def _source_prompt(question: str, context: str) -> str:
        return f"""DECISION QUESTION
{question.strip()}

USER CONTEXT
{context.strip() or "No additional context supplied."}
"""

    @classmethod
    def _evidence_prompt(
        cls, question: str, context: str, research: list[str]
    ) -> str:
        evidence = "\n\n".join(
            f"RESEARCH RESULT {index}\n{result}"
            for index, result in enumerate(research, start=1)
        )
        return f"""{cls._source_prompt(question, context)}

CURRENT WEB RESEARCH
{evidence}
"""
