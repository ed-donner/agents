"""Planner, search, writer, email agents and ResearchManager (async generator pipeline)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import os
from typing import Literal

import httpx
import sendgrid
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from pydantic import BaseModel, Field
from sendgrid.helpers.mail import Content, Email, Mail, To
import smtplib

import compat  # noqa: F401 — env + tracing before agent use
from agents import Agent, ModelSettings, Runner, WebSearchTool, function_tool, gen_trace_id, trace

HOW_MANY_SEARCHES = 3

# --- Planner ---

PLANNER_INSTRUCTIONS = (
    f"You are a helpful research assistant. Given a query (often including user clarifications "
    f"as Q&A), come up with web searches to best answer it. Respect scope, audience, and "
    f"constraints from any clarifications. Output {HOW_MANY_SEARCHES} terms to query for."
)


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model=compat.AGENT_MODEL,
    output_type=WebSearchPlan,
)

# --- Search ---

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

_use_openrouter_web_fallback = bool(os.getenv("OPENROUTER_API_KEY"))


@function_tool
async def web_search(query: str) -> str:
    """Search the web and return titles and snippets from top DuckDuckGo results."""
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AgentsCourse/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ) as client:
        response = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
        )
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    lines: list[str] = []
    for res in soup.select("div.result")[:10]:
        a = res.select_one("a.result__a")
        if not a:
            continue
        title = a.get_text(strip=True)
        snip = res.select_one(".result__snippet")
        snippet = snip.get_text(strip=True) if snip else ""
        lines.append(f"- {title}: {snippet}".strip())
    if not lines:
        return f"(No results parsed for {query!r}. Try a shorter query or check your network.)"
    return "\n".join(lines)


_search_tools = (
    [web_search]
    if _use_openrouter_web_fallback
    else [WebSearchTool(search_context_size="low")]
)
search_agent = Agent(
    name="Search agent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=_search_tools,
    model=compat.AGENT_MODEL,
    model_settings=ModelSettings(tool_choice="required"),
)

# --- Writer ---

WRITER_INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=compat.AGENT_MODEL,
    output_type=ReportData,
)

# --- Email ---


def _email_provider() -> Literal["gmail", "sendgrid"]:
    forced = (os.getenv("EMAIL_PROVIDER") or "").strip().lower()
    if forced == "gmail":
        if not (os.getenv("GMAIL_APP_PASSWORD") and os.getenv("GMAIL_ADDRESS")):
            raise ValueError("EMAIL_PROVIDER=gmail requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env")
        return "gmail"
    if forced == "sendgrid":
        if not os.getenv("SENDGRID_API_KEY"):
            raise ValueError("EMAIL_PROVIDER=sendgrid requires SENDGRID_API_KEY in .env")
        if not os.getenv("SENDGRID_FROM_EMAIL") or not os.getenv("SENDGRID_TO_EMAIL"):
            raise ValueError("EMAIL_PROVIDER=sendgrid requires SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL in .env")
        return "sendgrid"
    if os.getenv("GMAIL_APP_PASSWORD") and os.getenv("GMAIL_ADDRESS"):
        return "gmail"
    if os.getenv("SENDGRID_API_KEY"):
        if not os.getenv("SENDGRID_FROM_EMAIL") or not os.getenv("SENDGRID_TO_EMAIL"):
            raise ValueError(
                "SendGrid needs SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL — or add GMAIL_ADDRESS + GMAIL_APP_PASSWORD to use Gmail SMTP instead."
            )
        return "sendgrid"
    raise ValueError(
        "Set up email in .env: GMAIL_ADDRESS + GMAIL_APP_PASSWORD (Gmail), "
        "or SENDGRID_API_KEY + SENDGRID_FROM_EMAIL + SENDGRID_TO_EMAIL (SendGrid)."
    )


def send_lab_email(subject: str, body: str, *, subtype: Literal["plain", "html"] = "plain") -> None:
    prov = _email_provider()
    if prov == "gmail":
        user = os.environ["GMAIL_ADDRESS"].strip()
        pwd = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
        to_addr = (os.getenv("GMAIL_TO_EMAIL") or user).strip()
        msg = MIMEText(body, subtype, "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_addr
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(user, pwd)
            smtp.sendmail(user, [to_addr], msg.as_string())
        return
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL")
    to_addr = os.environ.get("SENDGRID_TO_EMAIL")
    if not from_addr or not to_addr:
        raise ValueError("SendGrid needs SENDGRID_FROM_EMAIL and SENDGRID_TO_EMAIL in .env")
    content_type = "text/html" if subtype == "html" else "text/plain"
    sg = sendgrid.SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"])
    mail = Mail(Email(from_addr), To(to_addr), subject, Content(content_type, body)).get()
    response = sg.client.mail.send.post(request_body=mail)
    if response.status_code >= 400:
        raise RuntimeError(f"SendGrid HTTP {response.status_code}: {response.body}")


@function_tool
def send_email(subject: str, html_body: str) -> str:
    """Send an email with the given subject and HTML body to the configured recipient."""
    send_lab_email(subject, html_body, subtype="html")
    return "success"


EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model=compat.AGENT_MODEL,
)

# --- Research manager ---


class ResearchManager:
    async def run(
        self,
        query: str,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ):
        """Run deep research; yield status lines then final markdown report."""

        async def _emit(line: str, *, log: bool = True) -> str:
            if log:
                print(line)
            if on_progress:
                await on_progress(line)
            return line

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            line = await _emit("Starting research...")
            yield line
            line = await _emit("Planning searches...")
            yield line
            search_plan = await self.plan_searches(query)
            n = len(search_plan.searches)
            line = await _emit(f"Will perform {n} searches")
            yield line
            line = await _emit("Searching...")
            yield line
            search_results = await self.perform_searches(search_plan, progress=on_progress)
            line = await _emit("Finished searching")
            yield line
            line = await _emit("Thinking about report...")
            yield line
            report = await self.write_report(query, search_results)
            line = await _emit("Finished writing report")
            yield line
            line = await _emit("Writing email...")
            yield line
            await self.send_email(report)
            line = await _emit("Email sent")
            yield line
            line = await _emit(report.markdown_report, log=False)
            yield line

    async def plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(
        self,
        search_plan: WebSearchPlan,
        progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> list[str]:
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        n = len(tasks)
        results: list[str] = []
        num_completed = 0
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            if progress:
                msg = f"Searching... "
                print(msg)
                await progress(msg)
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        inp = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, inp)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        inp = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, inp)
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)
