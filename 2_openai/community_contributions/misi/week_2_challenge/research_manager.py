import asyncio

from agents import Agent, Runner, function_tool

from clarification_agent import (
    ClarificationQuestions,
    RefinedQuery,
    clarification_agent,
    refinement_agent,
)
from planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from printer_agent import printer_agent
from search_agent import search_agent
from writer_agent import ReportData, writer_agent


MANAGER_INSTRUCTIONS = """
You are the research manager agent for a deep research workflow.

Your job is to orchestrate the full research process by calling your tools in this order:
1. Call `plan_searches` exactly once with the refined query.
2. Call `perform_searches` exactly once with the returned search plan.
3. Call `write_report` exactly once with the refined query and search results.
4. Call `print_report` exactly once using the markdown report from the generated report.
5. Return the full `ReportData` as your final answer.

Do not skip steps.
Do not invent search results.
Do not answer from your own knowledge when the tools can provide the data.
"""


async def get_clarification_questions(query: str) -> ClarificationQuestions:
    """Generate 3 clarification questions for the user's research topic."""
    print("Generating clarification questions...")
    result = await Runner.run(
        clarification_agent,
        f"User query: {query}",
    )
    print("Finished generating clarification questions")
    return result.final_output_as(ClarificationQuestions)


async def refine_query(query: str, questions: list[str], answers: list[str]) -> str:
    """Combine the original query and clarification answers into one refined query."""
    print("Refining query...")
    numbered_questions = "\n".join(
        f"{index}. {question}" for index, question in enumerate(questions, start=1)
    )
    numbered_answers = "\n".join(
        f"{index}. {answer}" for index, answer in enumerate(answers, start=1)
    )
    result = await Runner.run(
        refinement_agent,
        (
            f"Original query: {query}\n"
            f"Clarification questions:\n{numbered_questions}\n"
            f"User answers:\n{numbered_answers}"
        ),
    )
    print("Finished refining query")
    return result.final_output_as(RefinedQuery).refined_query


@function_tool
async def plan_searches(query: str) -> WebSearchPlan:
    """Create a web search plan for a refined research query."""
    print("Planning searches...")
    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )
    print(f"Will perform {len(result.final_output.searches)} searches")
    return result.final_output_as(WebSearchPlan)


async def search(item: WebSearchItem) -> str | None:
    """Perform one search from the plan."""
    input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
    try:
        result = await Runner.run(
            search_agent,
            input_text,
        )
        return str(result.final_output)
    except Exception:
        return None


@function_tool
async def perform_searches(search_plan: WebSearchPlan) -> list[str]:
    """Execute the planned searches and return summarized results."""
    print("Searching...")
    num_completed = 0
    tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
    results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        if result is not None:
            results.append(result)
        num_completed += 1
        print(f"Searching... {num_completed}/{len(tasks)} completed")
    print("Finished searching")
    return results


@function_tool
async def write_report(query: str, search_results: list[str]) -> ReportData:
    """Write the final research report from the refined query and search results."""
    print("Thinking about report...")
    input_text = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(
        writer_agent,
        input_text,
    )
    print("Finished writing report")
    return result.final_output_as(ReportData)


@function_tool
async def print_report(markdown_report: str) -> str:
    """Print a plain-text version of the markdown report."""
    print("Printing report...")
    await Runner.run(
        printer_agent,
        markdown_report,
    )
    print("Report printed")
    return "Report printed successfully."


research_manager = Agent(
    name="Research Manager",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[plan_searches, perform_searches, write_report, print_report],
    model="gpt-4o-mini",
    output_type=ReportData,
)
