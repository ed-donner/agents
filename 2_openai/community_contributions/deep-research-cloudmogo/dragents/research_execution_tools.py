import asyncio

from agents import Runner, function_tool

from dragents.email_sender_agent import email_agent
from dragents.perform_search_agent import search_agent
from dragents.report_gen_agent import report_writer_agent
from dragents.search_planner_agent import planner_agent
from models.models import Clarification, ReportData, SearchEvidence, WebSearchItem, WebSearchPlan


def format_clarification(clarification: Clarification | None) -> str:
    """Format clarification question and answer pairs for downstream prompts."""
    if clarification is None:
        return "None"

    lines = []
    for question, answer in zip(
        clarification.clarification_questions,
        clarification.clarification_answers,
    ):
        lines.append(f"Question: {question}")
        lines.append(f"Answer: {answer or '[No answer provided]'}")

    return "\n".join(lines) or "None"


def format_report_for_email(report: ReportData) -> str:
    """Format report sections into a single email-generation prompt."""
    follow_ups = "\n".join(
        f"- {question}" for question in report.follow_up_questions
    ) or "- None"

    return (
        "Create a polished HTML email from the report below.\n\n"
        f"Short summary:\n{report.short_summary}\n\n"
        f"Detailed markdown report:\n{report.markdown_report}\n\n"
        f"Follow-up questions:\n{follow_ups}"
    )


@function_tool
async def plan_searches_tool(
    original_query: str,
    clarification: Clarification | None = None,
) -> WebSearchPlan:
    """Create a search plan for the research task."""
    planner_input = (
        f"Query: {original_query}\n\n"
        "Clarification:\n"
        f"{format_clarification(clarification)}"
    )
    result = await Runner.run(planner_agent, planner_input)
    return result.final_output


async def _run_search(item: WebSearchItem) -> SearchEvidence:
    """Run one web search and convert it into structured evidence."""
    prompt = f"Search term: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(search_agent, prompt)
    return SearchEvidence(
        query=item.query,
        reason=item.reason,
        summary=result.final_output,
    )


@function_tool
async def perform_searches_tool(searches: list[WebSearchItem]) -> list[SearchEvidence]:
    """Execute a list of searches and return structured evidence."""
    tasks = [asyncio.create_task(_run_search(item)) for item in searches]
    return await asyncio.gather(*tasks)


@function_tool
async def write_report_tool(
    original_query: str,
    clarification: Clarification | None = None,
    evidence: list[SearchEvidence] | None = None,
) -> ReportData:
    """Generate the final report from structured evidence."""
    evidence = evidence or []
    evidence_blocks = []
    for item in evidence:
        evidence_blocks.append(
            f"Search Query: {item.query}\n"
            f"Why it mattered: {item.reason}\n"
            f"Summary: {item.summary}"
        )

    report_input = (
        f"Original Query: {original_query}\n\n"
        f"Clarification:\n{format_clarification(clarification)}\n\n"
        "Summarized search results:\n"
        f"{'\n\n'.join(evidence_blocks) if evidence_blocks else 'None'}"
    )
    result = await Runner.run(report_writer_agent, report_input)
    return result.final_output


@function_tool
async def send_report_email_tool(report: ReportData) -> str:
    """Send the report by email through the email specialist agent."""
    email_input = format_report_for_email(report)
    await Runner.run(email_agent, email_input)
    return "Email sent successfully."
