import gradio as gr
from agents import Agent, function_tool, Runner
import parameters as param

from planner_agent import planner_agent, WebSearchPlan
from search_agent import search_agent, SearchResults
from filter_agent import filter_agent, FilteredResults
from writer_agent import writer_agent, ReportData
from review_agent import review_agent, ReviewResult


@function_tool
async def plan_searches(query: str) -> WebSearchPlan:
    """ Plan the searches to perform for the query """
    print("Planning searches...")
    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )
    print("Plan completed\n")
    return result.final_output_as(WebSearchPlan)


@function_tool
async def perform_searches(query: str, search_plan: WebSearchPlan) -> SearchResults:
    """ Perform the searches from the search plan """
    print("\nSearching...")
    input = f"Original query: {query}\nSearch items: {search_plan}"
    result = await Runner.run(
        search_agent,
        input,
    )
    print("Searches completed\n")
    return result.final_output_as(SearchResults)


@function_tool
async def filter_searches(query: str, search_results: SearchResults) -> FilteredResults:
    """ Choose the most relevant search results for the query """
    print("\nFiltering...")
    input = f"Original query: {query}\nSearch results: {search_results}"
    result = await Runner.run(
            filter_agent,
            input,
        )
    print("Filtering completed\n")
    return result.final_output_as(FilteredResults)


@function_tool
async def write_report(query: str,
                    filtered_items: FilteredResults,
                    previous_draft: str,
                    feedback: list[str]) -> ReportData:
    """ Write the report for the query """
    print("\nThinking about report...")
    input = (
        f"Original query: {query}\n "
        f"Summarized search results: {filtered_items.results}\n "
        f"Previous draft of the report: {previous_draft}"
        f"Feedback from previous review: {feedback}"
    )
    result = await Runner.run(
        writer_agent,
        input,
    )
    print("Finished writing report\n")
    return result.final_output_as(ReportData)


@function_tool
async def review(query: str,
                search_results: FilteredResults,
                report: ReportData) -> ReviewResult:
    """ Review the report for errors and style """
    print("Reviewing report ...")
    input = ' '.join(
        [param.INSTRUCTIONS_REVIEW, 
        f"\nUser's Query: {query}",
        f"\nSearch results: {search_results}",
        f"\nReport: {report}",])
    
    result = await Runner.run(
        review_agent,
        input,
    )
    return result.final_output_as(ReviewResult)


# make sure the model spec is current
# publishing is handled deterministically by ReportManager after orchestration
orchestrator_agent = Agent[None](
    name="OrchestratorAgent",
    instructions= param.INSTRUCTIONS_ORCHESTRATOR,
    model= param.MODEL_ORCHESTRATOR,
    output_type=ReportData,
    tools=[
            plan_searches,
            perform_searches,
            filter_searches,
            write_report,
            review,
    ],
)