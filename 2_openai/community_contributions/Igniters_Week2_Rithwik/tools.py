import asyncio
from agents import Agent, Runner, Tool, function_tool
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent


@function_tool
async def plan_searches(query: str) -> WebSearchPlan:
    """Plan what web searches are needed to answer the research query."""
    result = await Runner.run(planner_agent, f"Query: {query}")
    return result.final_output_as(WebSearchPlan)


@function_tool
async def web_search(query: str, reason: str) -> str:
    """Perform a single web search. Call this multiple times in parallel for different searches."""
    input_text = f"Search term: {query}\nReason for searching: {reason}"
    try:
        result = await Runner.run(search_agent, input_text)
        return str(result.final_output)
    except Exception as e:
        return f"Search failed: {e}"


@function_tool
async def write_report(query: str, search_results: list[str]) -> ReportData:
    """Synthesise search results into a structured markdown report."""
    input_text = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(writer_agent, input_text)
    return result.final_output_as(ReportData)


@function_tool
async def send_email(markdown_report: str) -> str:
    """Send the finished report by email. Only call this once the report is complete."""
    await Runner.run(email_agent, markdown_report)
    return "Email sent successfully."