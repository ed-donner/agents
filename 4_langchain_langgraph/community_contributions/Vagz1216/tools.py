"""
tools.py — Function tools available to the research pipeline.

web_search uses DuckDuckGo so no paid search API key is needed.
send_report_email tries Resend first, then falls back to SendGrid.
All credentials come from environment variables — nothing is hardcoded.

To use Resend (recommended):
  RESEND_API_KEY=re_...
  RESEND_FROM_EMAIL=you@yourdomain.com   (must be a verified domain on resend.com)
  RESEND_TO_EMAIL=recipient@email.com

To use SendGrid (fallback):
  SENDGRID_API_KEY=SG....
  SENDGRID_FROM_EMAIL=you@yourdomain.com
  SENDGRID_TO_EMAIL=recipient@email.com
"""
from __future__ import annotations

import os

from ddgs import DDGS
from langchain_core.tools import tool


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


def _send_via_resend(subject: str, body: str) -> str:
    """Send email using Resend. Requires RESEND_API_KEY and RESEND_FROM_EMAIL."""
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    from_addr = os.environ.get("RESEND_FROM_EMAIL", "")
    to_addr   = os.environ.get("RESEND_TO_EMAIL",   "")
    params = resend.Emails.SendParams(
        from_=from_addr,
        to=[to_addr],
        subject=subject,
        html=body.replace("\n", "<br>"),
    )
    response = resend.Emails.send(params)
    return f"sent via Resend (id: {response['id']})"


def _send_via_sendgrid(subject: str, body: str) -> str:
    """Send email using SendGrid. Requires SENDGRID_API_KEY and SENDGRID_FROM_EMAIL."""
    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To
    api_key   = os.environ.get("SENDGRID_API_KEY", "")
    from_addr = os.environ.get("SENDGRID_FROM_EMAIL", "")
    to_addr   = os.environ.get("SENDGRID_TO_EMAIL",   "")
    sg   = sendgrid.SendGridAPIClient(api_key=api_key)
    mail = Mail(
        Email(from_addr), To(to_addr), subject,
        Content("text/html", body.replace("\n", "<br>")),
    )
    res = sg.client.mail.send.post(request_body=mail.get())
    return f"sent via SendGrid (status {res.status_code})"


def send_report_email(subject: str, body: str) -> str:
    """
    Send the research report by email.
    Tries Resend first (RESEND_API_KEY), falls back to SendGrid (SENDGRID_API_KEY).
    Returns a short status string written to ResearchState['email_status'].
    """
    if os.environ.get("RESEND_API_KEY"):
        try:
            return _send_via_resend(subject, body)
        except Exception as exc:
            # Resend failed — try SendGrid before giving up
            resend_err = str(exc)
    else:
        resend_err = "RESEND_API_KEY not set"

    if os.environ.get("SENDGRID_API_KEY"):
        try:
            return _send_via_sendgrid(subject, body)
        except Exception as exc:
            return f"error: Resend failed ({resend_err}), SendGrid also failed ({exc})"

    return "error: no email provider configured (set RESEND_API_KEY or SENDGRID_API_KEY)"
