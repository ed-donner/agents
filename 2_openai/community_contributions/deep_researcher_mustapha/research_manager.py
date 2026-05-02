"""
research_manager.py — Orchestrates the full 4-agent deep research pipeline.

Flow:
  1. PlannerAgent  → generate N search queries
  2. SearchAgent   → run all N searches in parallel
  3. WriterAgent   → synthesize results into a structured report
  4. EmailAgent    → send the report to the recipient

A `progress` async callback is called at each step so callers (e.g. FastAPI SSE)
can stream real-time status updates to the client.
"""
import asyncio
from typing import Callable, Awaitable, Optional

from agents import Runner, trace

from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from research_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from guard_agent import run_security_scan, GuardResult


# ── Individual step functions ─────────────────────────────────────────────────

async def plan_searches(query: str) -> WebSearchPlan:
    result = await Runner.run(planner_agent, f"Query: {query}")
    return result.final_output


async def _run_single_search(item: WebSearchItem) -> str:
    input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(search_agent, input_text)
    return result.final_output


async def perform_searches(search_plan: WebSearchPlan) -> list[str]:
    tasks = [asyncio.create_task(_run_single_search(item)) for item in search_plan.searches]
    return list(await asyncio.gather(*tasks))


async def write_report(query: str, search_results: list[str]) -> ReportData:
    input_text = f"Original query: {query}\n\nSummarized search results:\n" + "\n\n".join(search_results)
    result = await Runner.run(writer_agent, input_text)
    return result.final_output


async def send_report_email(
    report: ReportData,
    recipient: str,
    search_plan: Optional[WebSearchPlan] = None,
    search_results: Optional[list[str]] = None
) -> str:
    """Sends the report and the research process details to the recipient."""
    
    process_info = ""
    if search_plan and search_results:
        queries = "\n".join([f"- {s.query}" for s in search_plan.searches])
        results = "\n\n".join([f"### Source {i+1}\n{r}" for i, r in enumerate(search_results)])
        process_info = (
            "\n\n--- \n"
            "## Behind the Scenes: Research Process\n"
            "### Planned Search Queries\n"
            f"{queries}\n\n"
            "### Raw Findings & Evidence\n"
            f"{results}"
        )
    
    prompt = (
        f"FINAL REPORT:\n{report.markdown_report}\n\n"
        f"RESEARCH PROCESS DETAILS:\n{process_info}\n\n"
        f"Please send the email to: {recipient}"
    )
    result = await Runner.run(email_agent, prompt)
    return result.final_output


# ── Main orchestrator ─────────────────────────────────────────────────────────

ProgressCallback = Callable[[str, dict], Awaitable[None]]


async def run_deep_research(
    query: str,
    recipient_email: str,
    progress: Optional[ProgressCallback] = None,
) -> ReportData:
    """
    Run the full research pipeline.

    Args:
        query:           The research question to investigate.
        recipient_email: Where to send the final email report.
        progress:        Async callback(event_name, data_dict) for streaming updates.

    Returns:
        ReportData with short_summary, markdown_report, follow_up_questions.
    """

    async def emit(event: str, data: dict = None):
        if progress:
            await progress(event, data or {})

    with trace("Deep Research Web App"):

        # ── Step 1: Plan ──────────────────────────────────────────────────
        await emit("planning", {"message": "Planning search queries…"})
        search_plan = await plan_searches(query)
        await emit("planned", {
            "count": len(search_plan.searches),
            "queries": [s.query for s in search_plan.searches],
        })

        # ── Step 2: Search ────────────────────────────────────────────────
        await emit("searching", {
            "message": f"Running {len(search_plan.searches)} web searches in parallel…"
        })
        search_results = await perform_searches(search_plan)
        await emit("searched", {"message": "All searches complete."})

        # ── Step 3: Write ─────────────────────────────────────────────────
        await emit("writing", {"message": "Synthesising results into a report…"})
        report = await write_report(query, search_results)
        await emit("written", {"message": "Report ready."})

        # ── Step 4: Email ─────────────────────────────────────────────────
        await emit("emailing", {"message": f"Sending report to {recipient_email}…"})
        await send_report_email(report, recipient_email, search_plan, search_results)
        await emit("emailed", {"message": f"Email delivered to {recipient_email}!"})

        # ── Done ──────────────────────────────────────────────────────────
        await emit("done", {
            "short_summary": report.short_summary,
            "markdown_report": report.markdown_report,
            "follow_up_questions": report.follow_up_questions,
        })

    return report
