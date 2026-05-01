"""Content research pipeline: plan → search → write. Uses Gemini for planner/writer, OpenAI for search."""
import asyncio
from agents import Runner, trace, gen_trace_id
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from search_agent import search_agent
from writer_agent import writer_agent, ReportData


class ResearchManager:
    def __init__(self, audience: str = "", focus: str = ""):
        self.audience = audience or "general audience"
        self.focus = focus or ""

    async def run(self, query: str):
        """Run the research process; yields status updates then the final report."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield "Planning searches..."
            search_plan = await self._plan_searches(query)
            yield f"Running {len(search_plan.searches)} searches..."
            search_results = await self._perform_searches(search_plan)
            yield "Writing report..."
            report = await self._write_report(query, search_results)
            yield report

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self._search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            r = await task
            if r is not None:
                results.append(r)
        return results

    async def _search(self, item: WebSearchItem) -> str | None:
        inp = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(search_agent, inp)
            return str(result.final_output)
        except Exception:
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        context = f"Audience: {self.audience}. Focus: {self.focus}." if self.focus else f"Audience: {self.audience}."
        inp = f"Original query: {query}\n{context}\n\nSummarized search results:\n{search_results}"
        result = await Runner.run(writer_agent, inp)
        return result.final_output_as(ReportData)
