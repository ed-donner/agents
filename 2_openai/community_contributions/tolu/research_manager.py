"""Orchestrate education policy deep research: plan → parallel search → structured brief."""

import asyncio
from agents import Runner, gen_trace_id, trace
from policy_agents import (
    PolicyReportData,
    WebSearchPlan,
    planner_agent,
    search_agent,
    writer_agent,
)

class PolicyResearchManager:
    async def run(self, query: str):
        """Yield status lines, then the final markdown report body."""
        trace_id = gen_trace_id()
        with trace("Policy research trace", trace_id=trace_id):
            yield f"[status] Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "[status] Planning searches..."
            search_plan = await self.plan_searches(query)
            yield f"[status] Running {len(search_plan.searches)} searches..."
            search_results = await self.perform_searches(search_plan)
            yield "[status] Synthesizing policy brief..."
            report = await self.write_report(query, search_results)
            yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, f"Education policy research question: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self._one_search(item)) for item in search_plan.searches]
        results: list[str] = []
        for coro in asyncio.as_completed(tasks):
            out = await coro
            if out is not None:
                results.append(out)
        return results

    async def _one_search(self, item) -> str | None:
        prompt = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(search_agent, prompt)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> PolicyReportData:
        payload = (
            f"Original question: {query}\n\n"
            f"Search summaries ({len(search_results)}):\n{search_results}"
        )
        result = await Runner.run(writer_agent, payload)
        return result.final_output_as(PolicyReportData)