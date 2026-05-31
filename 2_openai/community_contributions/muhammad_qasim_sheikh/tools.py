from agents import Runner, function_tool
import asyncio

from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from search_evaluator_agent import search_evaluator_agent, SearchEvaluation
from report_evaluator_agent import report_evaluator_agent, ReportEvaluation

@function_tool
async def run_planning_step(query: str) -> WebSearchPlan:
    print("Tool Call: run_planning_step")
    result = await Runner.run(planner_agent, f"Query: {query}")
    return result.final_output_as(WebSearchPlan)

@function_tool
async def run_search_step(search_plan: WebSearchPlan) -> list[str]:
    print("Tool Call: run_search_step")
    
    async def search(item: WebSearchItem) -> str | None:
        input_prompt = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_prompt)
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed for query: {item.query} with error: {e}")
            return None

    tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
    results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        if result:
            results.append(result)
    
    print(f"Search Step Completed: {len(results)} results")
    return results

@function_tool
async def run_search_evaluation_step(query: str, search_results: list[str]) -> SearchEvaluation:
    print("Tool Call: run_search_evaluation_step")
    input_prompt = f"Original Query: {query}\n\nSearch Result Summaries:\n{search_results}"
    result = await Runner.run(search_evaluator_agent, input_prompt)
    return result.final_output_as(SearchEvaluation)

@function_tool
async def run_write_report_step(query: str, search_results: list[str], revisions_needed: str = "") -> ReportData:
    print("Tool Call: run_write_report_step")
    input_prompt = f"Original Query: {query}\n\nSummarized Search Results:\n{search_results}"
    if revisions_needed:
        input_prompt += f"\n\nIMPORTANT: This is a re-write. You must address the following revisions: {revisions_needed}"
        
    result = await Runner.run(writer_agent, input_prompt)
    print("Report Written")
    return result.final_output_as(ReportData)

@function_tool
async def run_report_evaluation_step(query: str, markdown_report: str) -> ReportEvaluation:
    print("Tool Call: run_report_evaluation_step")
    input_prompt = f"Original Query: {query}\n\nFull Report Draft:\n{markdown_report}"
    result = await Runner.run(report_evaluator_agent, input_prompt)
    return result.final_output_as(ReportEvaluation)

@function_tool
async def run_email_step(markdown_report: str) -> str:
    print("Tool Call: run_email_step")
    result = await Runner.run(email_agent, markdown_report)
    print("Email Sent")
    return "Email sent successfully."
