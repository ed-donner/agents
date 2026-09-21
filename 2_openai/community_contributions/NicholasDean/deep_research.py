"""Week 2 capstone (OpenAI Agents SDK) - a Deep Research agent.

The full week-2 pipeline, no shortcuts on the architecture:
  - an input GUARDRAIL screens the request before any work happens;
  - a Planner agent returns a STRUCTURED plan (output_type) of web searches;
  - Search agents run those searches IN PARALLEL (asyncio.gather) with the hosted WebSearchTool;
  - a Writer agent synthesizes a structured ReportData (summary + markdown + follow-ups);
  - an Email agent sends it via a send_report tool (SendGrid if SENDGRID_API_KEY is set, else it
    writes report.md so the pipeline always completes);
  - the whole run is wrapped in one trace() for observability.

Run: uv run python deep_research.py "your research question"
     (needs OPENAI_API_KEY; WebSearchTool bills per search; SENDGRID_API_KEY optional)
"""
import asyncio
import os
import sys
from pathlib import Path

from agents import (Agent, GuardrailFunctionOutput, InputGuardrailTripwireTriggered, Runner,
                    WebSearchTool, function_tool, input_guardrail, trace)
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)
HOW_MANY = 3


# ---- structured outputs ----
class WebSearchItem(BaseModel):
    reason: str = Field(description="why this search helps answer the query")
    query: str = Field(description="the search term to run")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]


class ReportData(BaseModel):
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]


# ---- input guardrail: refuse disallowed research up front ----
class SafetyCheck(BaseModel):
    is_disallowed: bool
    reason: str


guardrail_agent = Agent(
    name="Guardrail",
    instructions="Decide if the research request is disallowed: doxxing or finding private personal "
                 "information about a private individual, or clearly harmful/illegal instructions. "
                 "Normal public-interest research is allowed.",
    model="gpt-4o-mini",
    output_type=SafetyCheck,
)


@input_guardrail
async def safety_guardrail(ctx, agent, user_input):
    check = (await Runner.run(guardrail_agent, user_input)).final_output
    return GuardrailFunctionOutput(output_info=check, tripwire_triggered=check.is_disallowed)


# ---- agents ----
planner_agent = Agent(
    name="Planner",
    instructions=f"You plan web research. Given a query, output {HOW_MANY} focused searches that "
                 "together answer it.",
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
    input_guardrails=[safety_guardrail],
)

search_agent = Agent(
    name="Searcher",
    instructions="Search the web for the term and write a concise 2-3 paragraph summary (<300 words) "
                 "of what you found. No preamble.",
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="low")],
)

writer_agent = Agent(
    name="Writer",
    instructions="Given the query and the search summaries, write a cohesive markdown report, a "
                 "one-sentence summary, and a few follow-up questions.",
    model="gpt-4o-mini",
    output_type=ReportData,
)


@function_tool
def send_report(subject: str, markdown_body: str) -> str:
    """Email the report. Uses SendGrid if SENDGRID_API_KEY is set; otherwise writes report.md."""
    if os.getenv("SENDGRID_API_KEY"):
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        sg.send(Mail(from_email=os.getenv("FROM_EMAIL", "me@example.com"),
                     to_emails=os.getenv("TO_EMAIL", "me@example.com"),
                     subject=subject, html_content=markdown_body))
        return "sent via SendGrid"
    Path("report.md").write_text(f"# {subject}\n\n{markdown_body}", encoding="utf-8")
    return "wrote report.md (set SENDGRID_API_KEY to email instead)"


email_agent = Agent(
    name="Emailer",
    instructions="You are given a report. Call send_report with a clear subject and the markdown body.",
    model="gpt-4o-mini",
    tools=[send_report],
)


# ---- orchestration ----
async def research(query: str) -> ReportData:
    with trace("Deep research"):
        plan = (await Runner.run(planner_agent, query)).final_output          # structured plan (guarded)
        summaries = await asyncio.gather(*[                                   # searches in parallel
            Runner.run(search_agent, f"Term: {s.query}\nReason: {s.reason}") for s in plan.searches
        ])
        findings = "\n\n".join(r.final_output for r in summaries)
        report = (await Runner.run(writer_agent, f"Query: {query}\n\nFindings:\n{findings}")).final_output
        await Runner.run(email_agent, f"Subject hint: {query}\n\n{report.markdown_report}")
        return report


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What are the main agentic AI frameworks in 2025?"
    try:
        report = asyncio.run(research(q))
        print(report.short_summary)
        print("\n(full report emailed, or saved to report.md)")
    except InputGuardrailTripwireTriggered:
        print("Request blocked by the input guardrail.")
