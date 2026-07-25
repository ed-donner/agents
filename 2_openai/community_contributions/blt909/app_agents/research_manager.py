from agents import Runner, Agent, function_tool
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from query_guardrail import query_clarity_guardrail
import asyncio

@function_tool
async def plan_searches(query: str) -> WebSearchPlan:
    """Plan the searches to perform for the query."""
    print("Planning searches...")
    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )
    plan = result.final_output_as(WebSearchPlan)
    print(f"Will perform {len(plan.searches)} searches")
    return plan

@function_tool
async def perform_searches(searches: list[WebSearchItem]) -> list[str]:
    """Perform a list of searches and return the summarized results."""
    print("Searching...")
    async def search(item: WebSearchItem) -> str | None:
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_text)
            return str(result.final_output)
        except Exception:
            return None

    tasks = [asyncio.create_task(search(s)) for s in searches]
    results = []
    num_completed = 0
    for task in asyncio.as_completed(tasks):
        res = await task
        if res is not None:
            results.append(res)
        num_completed += 1
        print(f"Searching... {num_completed}/{len(tasks)} completed")
    print("Finished searching")
    return results

@function_tool
async def write_newsletter(query: str, search_results: list[str]) -> ReportData:
    """Write the newsletter for the query based on search results."""
    print("Thinking about report...")
    input_text = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(
        writer_agent,
        input_text,
    )
    print("Finished writing report")
    report = result.final_output_as(ReportData)
    return report

INSTRUCTIONS = (
    "You are a research manager orchestrating a newsletter generation pipeline. "
    "Before you run, a query clarity guardrail will automatically evaluate the user query — "
    "if the query is too vague, it will halt execution and ask the user for clarification.\n\n"
    "Once the query is clear, follow these steps exactly:\n"
    "1. Use the 'plan_searches' tool to generate a set of targeted web searches for the query.\n"
    "2. Use the 'perform_searches' tool to execute all planned searches concurrently and collect results.\n"
    "3. Use the 'write_newsletter' tool to draft a detailed markdown newsletter from the search results.\n"
    "4. Hand off to the Email agent to convert the newsletter to HTML and send it to the recipient."
)

research_manager_agent = Agent(
    name="Research Manager",
    instructions=INSTRUCTIONS,
    model="gpt-4o",
    tools=[plan_searches, perform_searches, write_newsletter],
    handoffs=[email_agent],
    input_guardrails=[query_clarity_guardrail],
)