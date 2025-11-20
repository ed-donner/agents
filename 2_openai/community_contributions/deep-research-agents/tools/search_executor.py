from schema import WebSearchPlan, SearchResult, ExecutedSearchPlan
from ai_agents.search_agent import run_search
from agents import function_tool
import asyncio


@function_tool
async def execute_search_plan(plan: WebSearchPlan) -> ExecutedSearchPlan:
    """Executes all queries in a WebSearchPlan in parallel and returns their summaries."""
    tasks = [run_search(q) for q in plan.searches]
    summaries = await asyncio.gather(*tasks)

    results = [
        SearchResult(query=plan.searches[i].query, summary=summaries[i])
        for i in range(len(plan.searches))
    ]

    print('[execute_search_plan]:', results)

    return ExecutedSearchPlan(results=results)
