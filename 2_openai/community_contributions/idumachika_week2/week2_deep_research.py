"""
Week 2 assessment — Deep Research pipeline (extends 4_lab4) with:
  • Clarifying-questions step before search planning (enriched research brief)
  • Structured EmailDraft for HTML email (Lab 3 exercise: structured email generation)
  • Parallel web search, writer with ReportData, optional SendGrid delivery
  • Report always written to week2_report_output.md next to this file

Run from repo root:
  uv run python 2_openai/community_contributions/idumachika_week2/week2_deep_research.py "Your topic"

Env (optional):
  SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_TO_EMAIL — send email; else skip send
  CLARIFY_ANSWERS — multiline answers to clarifying questions (same order as printed)
  SKIP_CLARIFICATION=1 — skip clarification agent

OpenAI WebSearchTool incurs per-call cost; see 4_lab4 notebook.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import Any

import sendgrid
from agents import Agent, ModelSettings, Runner, WebSearchTool, trace
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sendgrid.helpers.mail import Content, Email, Mail, To

load_dotenv(override=True)

MODEL = "gpt-4o-mini"
HOW_MANY_SEARCHES = 3

_DIR = Path(__file__).resolve().parent
REPORT_PATH = _DIR / "week2_report_output.md"


# --- Structured outputs (labs 3–4) ---


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the query.")
    query: str = Field(description="Search term for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="Web searches to perform to answer the query."
    )


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Short clarifying questions to narrow scope (1–5 items)."
    )


class ReportData(BaseModel):
    short_summary: str = Field(description="2–3 sentence summary of findings.")
    markdown_report: str = Field(description="Full markdown report.")
    follow_up_questions: list[str] = Field(
        description="Suggested follow-up research topics."
    )


class EmailDraft(BaseModel):
    """Structured email (Lab 3 exercise: structured outputs for email)."""

    subject: str = Field(description="Clear, professional email subject line.")
    html_body: str = Field(
        description="Complete HTML email body with headings and readable layout."
    )


# --- Agents ---


SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, search the web and produce a concise "
    "summary of the results (2–3 short paragraphs, under 300 words). Capture main points; "
    "succinct phrasing is fine. No preamble—summary only."
)

search_agent = Agent(
    name="Search agent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model=MODEL,
    model_settings=ModelSettings(tool_choice="required"),
)

PLANNER_INSTRUCTIONS = (
    f"You are a research planner. Given a research brief, propose exactly {HOW_MANY_SEARCHES} "
    "web searches that together best answer the brief. "
    "Each search must have a clear reason and a focused query string."
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model=MODEL,
    output_type=WebSearchPlan,
)

clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=(
        "You are a research intake assistant. Given the user's research topic, "
        "produce 2–4 concise clarifying questions that would improve depth and focus. "
        "Avoid duplicating what is already explicit in the topic."
    ),
    model=MODEL,
    output_type=ClarifyingQuestions,
)

WRITER_INSTRUCTIONS = (
    "You are a senior researcher. You receive the original brief and summarized search results. "
    "First outline the report structure mentally, then write a cohesive markdown report. "
    "Aim for at least 1000 words when the material supports it; be substantive and specific. "
    "Include a short summary and follow-up questions in the structured output fields."
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=MODEL,
    output_type=ReportData,
)

email_formatter = Agent(
    name="EmailFormatter",
    instructions=(
        "Convert the given markdown research report into a single professional HTML email. "
        "Use clear headings, lists where helpful, and a restrained style suitable for "
        "a business reader. Output only via the structured fields."
    ),
    model=MODEL,
    output_type=EmailDraft,
)


def build_enriched_query(
    query: str, questions: list[str], answers_text: str) -> str:
    if not questions:
        return query
    answers_text = (answers_text or "").strip()
    if not answers_text:
        lines = [f"Original research topic:\n{query}\n", "Context (clarifications not provided):"]
        for q in questions:
            lines.append(f"- {q} → (not specified)")
        return "\n".join(lines)
    parts = [p.strip() for p in answers_text.split("\n---\n")]
    lines = [
        f"Original research topic:\n{query}\n",
        "Clarifying Q&A:",
    ]
    for i, q in enumerate(questions):
        ans = parts[i] if i < len(parts) else "(not specified)"
        lines.append(f"Q: {q}\nA: {ans}\n")
    return "\n".join(lines)


async def clarify(query: str) -> ClarifyingQuestions:
    r = await Runner.run(clarification_agent, f"User research topic:\n{query}")
    return r.final_output_as(ClarifyingQuestions)


async def plan_searches(brief: str) -> WebSearchPlan:
    print("Planning searches…", flush=True)
    r = await Runner.run(planner_agent, f"Research brief:\n{brief}")
    return r.final_output_as(WebSearchPlan)


async def search_one(item: WebSearchItem) -> str:
    text = f"Search term: {item.query}\nReason: {item.reason}"
    r = await Runner.run(search_agent, text)
    return str(r.final_output)


async def perform_searches(plan: WebSearchPlan) -> list[str]:
    print(f"Running {len(plan.searches)} searches in parallel…", flush=True)
    tasks = [asyncio.create_task(search_one(item)) for item in plan.searches]
    return await asyncio.gather(*tasks)


async def write_report(brief: str, search_results: list[str]) -> ReportData:
    print("Writing report…", flush=True)
    payload = f"Research brief:\n{brief}\n\nSummarized search results:\n{search_results}\n"
    r = await Runner.run(writer_agent, payload)
    return r.final_output_as(ReportData)


def write_report_file(report: ReportData) -> None:
    text = (
        f"# Week 2 deep research output\n\n"
        f"## Summary\n\n{report.short_summary}\n\n"
        f"## Report\n\n{report.markdown_report}\n\n"
        f"## Follow-up ideas\n\n"
        + "\n".join(f"- {q}" for q in report.follow_up_questions)
    )
    REPORT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}", flush=True)


def send_email_html(subject: str, html_body: str) -> dict[str, Any]:
    key = os.environ.get("SENDGRID_API_KEY")
    if not key:
        print("SENDGRID_API_KEY not set — skipping email send.", flush=True)
        return {"status": "skipped"}

    from_addr = os.environ.get("SENDGRID_FROM_EMAIL", "you@example.com")
    to_addr = os.environ.get("SENDGRID_TO_EMAIL", from_addr)

    sg = sendgrid.SendGridAPIClient(api_key=key)
    mail = Mail(
        Email(from_addr),
        To(to_addr),
        subject,
        Content("text/html", html_body),
    ).get()
    sg.client.mail.send.post(request_body=mail)
    print("Email sent via SendGrid.", flush=True)
    return {"status": "sent"}


async def format_email(report_md: str) -> EmailDraft:
    print("Formatting structured email…", flush=True)
    r = await Runner.run(email_formatter, report_md)
    return r.final_output_as(EmailDraft)


async def run_pipeline(
    query: str,
    *,
    skip_clarification: bool,
    clarify_answers: str | None,
) -> None:
    brief = query
    if not skip_clarification:
        cq = await clarify(query)
        print("Clarifying questions:", flush=True)
        for i, q in enumerate(cq.questions, 1):
            print(f"  {i}. {q}", flush=True)
        answers = clarify_answers or ""
        brief = build_enriched_query(query, cq.questions, answers)

    plan = await plan_searches(brief)
    results = await perform_searches(plan)
    report = await write_report(brief, results)
    write_report_file(report)

    draft = await format_email(report.markdown_report)
    send_email_html(draft.subject, draft.html_body)


def main() -> None:
    p = argparse.ArgumentParser(description="Week 2 deep research pipeline")
    p.add_argument("query", nargs="?", default=os.getenv("RESEARCH_QUERY", ""))
    p.add_argument(
        "--skip-clarification",
        action="store_true",
        help="Skip clarification agent (useful for quick runs).",
    )
    args = p.parse_args()
    query = (args.query or "").strip()
    if not query:
        p.error("Provide a research topic as an argument or set RESEARCH_QUERY.")

    skip = args.skip_clarification or os.getenv("SKIP_CLARIFICATION", "") == "1"
    answers = os.getenv("CLARIFY_ANSWERS")

    async def _run() -> None:
        with trace("Week2 Deep Research — idumachika"):
            await run_pipeline(
                query,
                skip_clarification=skip,
                clarify_answers=answers,
            )

    asyncio.run(_run())


if __name__ == "__main__":
    main()
