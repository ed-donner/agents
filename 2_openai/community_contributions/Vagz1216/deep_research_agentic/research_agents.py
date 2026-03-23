"""
All agent definitions for the deep research pipeline.

Design pattern (from 2_openai labs):
  - Workers are individual Agents with focused instructions and ModelSettings.
  - The orchestrator exposes workers as tools via .as_tool() and @function_tool,
    then hands off to the email agent for final delivery.

Provider note:
  - WebSearchTool (OpenAI-hosted) is NOT used here so this pipeline works with
    any OpenAI-compatible provider (Groq, OpenRouter, OpenAI).
  - Web search is handled by a @function_tool backed by DuckDuckGo (no API key).
  - All agents use DEFAULT_MODEL from config.py — change provider there.
"""
from __future__ import annotations

import os

import sendgrid
from ddgs import DDGS
from sendgrid.helpers.mail import Content, Email, Mail, To

from agents import Agent, ModelSettings, function_tool
from config import DEFAULT_MODEL
from models import (
    ClarifyingQuestions,
    ReportData,
    ReportEvaluation,
    ResearchSufficiencyCheck,
    WebSearchPlan,
)

# ---------------------------------------------------------------------------
# Shared ModelSettings — sampling parameters required by PR checklist
# ---------------------------------------------------------------------------
DEFAULT_SETTINGS = ModelSettings(
    temperature=0.3,
    max_tokens=4096,
    top_p=0.95,
)

SEARCH_SETTINGS = ModelSettings(
    temperature=0.1,       # low temperature: factual retrieval, no hallucination
    max_tokens=2048,
    top_p=0.9,
)

CREATIVE_SETTINGS = ModelSettings(
    temperature=0.6,       # slightly higher: fluent, varied prose
    max_tokens=4096,       # kept under free-tier limits on OpenRouter
    top_p=0.95,
)

# ---------------------------------------------------------------------------
# Web search tool — DuckDuckGo (free, no API key, works with any provider)
# Replaces WebSearchTool which is OpenAI-hosted and requires an OpenAI key.
# ---------------------------------------------------------------------------
@function_tool
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo and return a formatted summary of the
    top results. Returns up to 5 results with title, snippet, and source URL.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return f"No results found for query: {query}"

        sections = []
        for r in results:
            sections.append(
                f"**{r.get('title', 'No title')}**\n"
                f"{r.get('body', '')}\n"
                f"Source: {r.get('href', '')}"
            )
        return "\n\n---\n\n".join(sections)

    except Exception as exc:
        return f"Search error for '{query}': {exc}"


# ---------------------------------------------------------------------------
# 1. Clarifier — produces 3 scoping questions
# ---------------------------------------------------------------------------
clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=(
        "You are a research scoping specialist. Given a research query, generate exactly "
        "three concise clarifying questions that will most sharpen the scope and focus of "
        "the research. Also provide a one-sentence summary of what you already understand "
        "from the query. Do not answer the questions yourself."
    ),
    model=DEFAULT_MODEL,
    model_settings=DEFAULT_SETTINGS,
    output_type=ClarifyingQuestions,
)

# ---------------------------------------------------------------------------
# 2. Planner — turns query + clarifications into a prioritised search plan
# ---------------------------------------------------------------------------
planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You are a research planning specialist. Given an original query and any user "
        "clarifications, produce a focused set of 5–8 web search terms. Assign each a "
        "priority (1=critical, 2=important, 3=nice-to-have). Prioritise breadth first, "
        "then depth on the most critical angles. Avoid redundant or overlapping queries."
    ),
    model=DEFAULT_MODEL,
    model_settings=DEFAULT_SETTINGS,
    output_type=WebSearchPlan,
)

# ---------------------------------------------------------------------------
# 3. Search — executes a single web search and summarises the results
# ---------------------------------------------------------------------------
search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You are a web research assistant. Given a search term, use your web_search tool "
        "to look it up and produce a concise 2–3 paragraph summary (≤300 words). "
        "Capture key facts, figures, and source context. Write in note-taking style — "
        "no filler, no commentary beyond the summary itself. Always call the tool."
    ),
    model=DEFAULT_MODEL,
    model_settings=SEARCH_SETTINGS,
    tools=[web_search],
)

# ---------------------------------------------------------------------------
# 4. Sufficiency checker — decides whether more research is needed
# ---------------------------------------------------------------------------
sufficiency_agent = Agent(
    name="SufficiencyAgent",
    instructions=(
        "You are a research quality auditor. Given the original query, user clarifications, "
        "and accumulated search results, decide whether the evidence is sufficient to write "
        "a thorough, balanced report. If gaps exist, specify missing angles and suggest up "
        "to 3 additional search queries to fill them. Be strict — only approve when coverage "
        "is genuinely comprehensive."
    ),
    model=DEFAULT_MODEL,
    model_settings=DEFAULT_SETTINGS,
    output_type=ResearchSufficiencyCheck,
)

# ---------------------------------------------------------------------------
# 5. Writer — synthesises search results into a long-form report
# ---------------------------------------------------------------------------
writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a senior research analyst. Given an original query, user clarifications, "
        "and summarised search results, produce a detailed, well-structured Markdown report "
        "(aim for 1,000–2,000 words). Structure: executive summary, background, key findings "
        "(with sub-sections), analysis, conclusions, and suggested next steps. "
        "Cite sources inline where possible. End with a list of follow-up questions."
    ),
    model=DEFAULT_MODEL,
    model_settings=CREATIVE_SETTINGS,
    output_type=ReportData,
)

# ---------------------------------------------------------------------------
# 6. Evaluator — scores the report and decides approve / revise
# ---------------------------------------------------------------------------
evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=(
        "You are a research quality evaluator. Given a research report and the original "
        "query, score the report 0–10 and decide whether to approve it. Approve (score ≥ 7) "
        "only if: the report fully addresses the query, is factually grounded, is well "
        "structured, and is at least 800 words. For scores below 7, provide specific, "
        "actionable improvement suggestions so the writer can revise."
    ),
    model=DEFAULT_MODEL,
    model_settings=DEFAULT_SETTINGS,
    output_type=ReportEvaluation,
)

# ---------------------------------------------------------------------------
# 7. Email delivery agent — converts Markdown to HTML and sends via SendGrid
# ---------------------------------------------------------------------------
@function_tool
def send_report_email(subject: str, html_body: str) -> str:
    """Send the research report as a formatted HTML email via SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL", "martin@markethacks.co.ke")
    to_addr = os.environ.get("SENDGRID_TO_EMAIL", "myskill254@gmail.com")

    if not api_key:
        return "error: SENDGRID_API_KEY not set"

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        mail = Mail(
            from_email=Email(from_addr),
            to_emails=To(to_addr),
            subject=subject,
            html_content=Content("text/html", html_body),
        )
        response = sg.client.mail.send.post(request_body=mail.get())
        return f"sent (status {response.status_code})"
    except Exception as exc:
        return f"error: {exc}"


email_agent = Agent(
    name="EmailAgent",
    instructions=(
        "You are an email formatting specialist. Given a Markdown research report, convert "
        "it into clean, well-structured HTML and send it as a single email with a descriptive "
        "subject line using your tool. Keep the HTML readable: use headings, paragraphs, and "
        "a simple colour scheme. Do not add any commentary outside the email."
    ),
    model=DEFAULT_MODEL,
    model_settings=DEFAULT_SETTINGS,
    tools=[send_report_email],
)
