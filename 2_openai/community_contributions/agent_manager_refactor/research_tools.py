from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from questions_generator_agent import questions_generator_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
from agents import function_tool

"""
    async def run(self, query: str):
        " Run the deep research process, yielding the status updates and the final report"
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan_result = await self.plan_searches(query)
            search_plan = search_plan_result.searches
            user_email = search_plan_result.user_email
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report, user_email)
            yield "Email sent, research complete"
            yield report.markdown_report
"""

@function_tool
async def generate_questions(query: str) -> str:
    """ Generate 5 questions to answer for the query """
    print("Generating questions...")
    result = await Runner.run(
        questions_generator_agent,
        f"Query: {query}",
    )
    print(f"Generated 5 questions...")
    return result.final_output

@function_tool
async def plan_searches(query: str) -> WebSearchPlan:
    """ Plan the searches to perform for the query """
    print("Planning searches...")
    result = await Runner.run(
        planner_agent,
        f"Query: {query}",
    )
    print(f"Will perform {len(result.final_output.searches)} searches")
    return result.final_output_as(WebSearchPlan)

@function_tool
async def perform_searches(search_plan: WebSearchPlan) -> list[str]:
    """ Perform the searches to perform for the query """
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

@function_tool
async def write_report(query: str, search_results: list[str]) -> ReportData:
    """ Write the report for the query """
    print("Thinking about report...")
    input = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(
        writer_agent,
        input,
    )

    print("Finished writing report")
    return result.final_output_as(ReportData)
    
@function_tool
async def send_email(report: ReportData, user_email: str) -> None:
    print("Writing email...")
    result = await Runner.run(
        email_agent,
        f"Report: {report.markdown_report}\nUser email: {user_email}",
    )
    print("Email sent")
    return report