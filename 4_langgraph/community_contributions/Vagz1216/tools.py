"""
tools.py — Function tools available to the research pipeline.

web_search uses DuckDuckGo so no paid search API key is needed.
send_report_email uses SendGrid; all credentials come from environment variables.
"""
from __future__ import annotations

import os

import sendgrid
from ddgs import DDGS
from langchain_core.tools import tool
from sendgrid.helpers.mail import Content, Email, Mail, To


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo. Returns top 5 results with title, snippet and URL.
    Works with any LLM provider — no OpenAI key required."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No results found for: {query}"
        return "\n\n---\n\n".join(
            f"{r.get('title', '')}\n{r.get('body', '')}\nSource: {r.get('href', '')}"
            for r in results
        )
    except Exception as exc:
        return f"Search error for '{query}': {exc}"


def send_report_email(subject: str, body: str) -> str:
    """Send the research report as an HTML email via SendGrid.
    All credentials are read from environment variables — nothing hardcoded."""
    api_key   = os.environ.get("SENDGRID_API_KEY")
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL", "sender@example.com")
    to_addr   = os.environ.get("SENDGRID_TO_EMAIL",   "recipient@example.com")
    if not api_key:
        return "error: SENDGRID_API_KEY not set"
    try:
        sg   = sendgrid.SendGridAPIClient(api_key=api_key)
        mail = Mail(
            Email(from_addr), To(to_addr), subject,
            Content("text/html", body.replace("\n", "<br>"))
        )
        res = sg.client.mail.send.post(request_body=mail.get())
        return f"sent (status {res.status_code})"
    except Exception as exc:
        return f"error: {exc}"
