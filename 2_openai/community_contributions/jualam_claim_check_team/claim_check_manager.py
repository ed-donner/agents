import asyncio

from agents import Runner, gen_trace_id, trace

from research_agents import SearchItem, SearchPlan, planner_agent, research_agent
from review_agents import EvidenceReview, review_agents
from verdict_agent import ClaimVerdict, verdict_agent


class ClaimCheckManager:
    async def run(self, claim: str, context: str):
        trace_id = gen_trace_id()
        with trace("Claim check workflow", trace_id=trace_id):
            yield "Planning independent searches to test the claim..."
            plan = await self._plan(claim, context)

            yield f"Running {len(plan.searches)} evidence searches in parallel..."
            research = await self._research(plan)

            yield "Evidence collected. Running evidence, skepticism, and source-quality reviews..."
            reviews = await self._review(claim, context, research)

            yield "Reviews complete. Calibrating the final verdict..."
            verdict = await self._write_verdict(claim, context, research, reviews)

            yield verdict.to_markdown()

    async def _plan(self, claim: str, context: str) -> SearchPlan:
        result = await Runner.run(planner_agent, self._claim_prompt(claim, context))
        return result.final_output

    async def _research(self, plan: SearchPlan) -> list[str]:
        return await asyncio.gather(*(self._search(item) for item in plan.searches))

    async def _search(self, item: SearchItem) -> str:
        prompt = f"Verification query: {item.query}\nPurpose: {item.purpose}"
        result = await Runner.run(research_agent, prompt)
        return result.final_output

    async def _review(
        self, claim: str, context: str, research: list[str]
    ) -> list[EvidenceReview]:
        evidence = self._evidence_prompt(claim, context, research)
        results = await asyncio.gather(
            *(Runner.run(agent, evidence) for agent in review_agents)
        )
        return [result.final_output for result in results]

    async def _write_verdict(
        self,
        claim: str,
        context: str,
        research: list[str],
        reviews: list[EvidenceReview],
    ) -> ClaimVerdict:
        review_data = "\n\n".join(review.model_dump_json(indent=2) for review in reviews)
        prompt = f"""{self._evidence_prompt(claim, context, research)}

INDEPENDENT REVIEWS
{review_data}
"""
        result = await Runner.run(verdict_agent, prompt)
        return result.final_output

    @staticmethod
    def _claim_prompt(claim: str, context: str) -> str:
        return f"""CLAIM
{claim.strip()}

USER CONTEXT
{context.strip() or "No additional context supplied."}
"""

    @classmethod
    def _evidence_prompt(cls, claim: str, context: str, research: list[str]) -> str:
        evidence = "\n\n".join(
            f"RESEARCH RESULT {index}\n{result}"
            for index, result in enumerate(research, start=1)
        )
        return f"""{cls._claim_prompt(claim, context)}

WEB RESEARCH
{evidence}
"""
