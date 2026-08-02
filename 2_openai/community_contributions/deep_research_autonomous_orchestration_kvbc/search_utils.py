from search_agent import search_agent
import asyncio
from planner_agent import WebSearchPlan, WebSearchItem, planner_agent
from search_agent import search_agent
from agents import Runner



async def plan_searches( query: str, previous_searchplan:WebSearchPlan = None) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        previous = f", previous searches: {previous_searchplan.searches}" if previous_searchplan else ""
        result = await Runner.run(
            planner_agent,
            f"Query: {query}{previous}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

async def perform_searches(search_plan: WebSearchPlan, previous_results: list[str]|None=None) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
        results = list(previous_results) if previous_results else []

        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results


async def search(item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None