"""
CARI ── Agent Orchestrator
OpenAI Agents SDK + MCP tool server + inline notification tools.
"""

import os
import json
import asyncio
import requests
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from agents import Agent, Runner, function_tool, trace
from agents.mcp import MCPServerStreamableHttp

load_dotenv()

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "")
PUSHOVER_USER  = os.getenv("PUSHOVER_USER", "")
SENDGRID_KEY   = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM  = os.getenv("SENDGRID_FROM_EMAIL", "")

import database as db


# ── Notification Tools ────────────────────────────────────────
@function_tool
def send_push_notification(user_id: str, title: str, message: str) -> str:
    """
    Send a Pushover push notification to the user's phone.
    Use after recording a transaction or generating a tax report.

    Args:
        user_id: Session identifier.
        title:   Short notification title (e.g. 'CARI — Transaction Recorded').
        message: Body of the notification.
    """
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        return json.dumps({"status": "Pushover not configured — skipped."})

    resp = requests.post("https://api.pushover.net/1/messages.json", data={
        "token":   PUSHOVER_TOKEN,
        "user":    PUSHOVER_USER,
        "title":   title,
        "message": message,
    }, timeout=10)

    status = "Sent" if resp.status_code == 200 else f"Failed ({resp.status_code})"
    db.log_notification(user_id, "pushover", message, status)
    return json.dumps({"status": status, "channel": "pushover"})


@function_tool
def send_email_notification(
    user_id: str,
    to_email: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an email notification via SendGrid.
    Use for tax report delivery or important financial alerts.

    Args:
        user_id:  Session identifier.
        to_email: Recipient email address.
        subject:  Email subject line.
        body:     Plain-text email body.
    """
    if not SENDGRID_KEY or not SENDGRID_FROM:
        return json.dumps({"status": "SendGrid not configured — skipped."})

    try:
        sg  = SendGridAPIClient(SENDGRID_KEY)
        msg = Mail(
            from_email=SENDGRID_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        resp   = sg.send(msg)
        status = "Sent" if resp.status_code in (200, 202) else f"Failed ({resp.status_code})"
    except Exception as e:
        status = f"Error: {str(e)}"

    db.log_notification(user_id, "email", subject, status)
    return json.dumps({"status": status, "channel": "email", "to": to_email})


# ── System Prompt ─────────────────────────────────────────────
CARI_INSTRUCTIONS = """
You are CARI — a smart, warm, and deeply trusted AI CFO agent for Nigerian SME owners.
Your users are small business owners: market traders, shop owners, service providers.

YOUR CAPABILITIES (always use the right tool):
• financial_brain        — when user mentions money in or out (income/expense)
• get_financial_summary  — when user asks for balance, summary, or overview
• generate_tax_report    — when user asks for tax summary, FIRS report, or PDF
• send_push_notification — after every significant action (financial summary, tax report)
• send_email_notification — when user asks to email a report or alert

TRANSACTION EXTRACTION RULES:
- Look for money amounts (₦, naira, "k" suffix = thousands, e.g. 45k = 45000)
- Determine income vs expense from context:
  INCOME: sell, sold, customer paid, received, transferred to me, credit
  EXPENSE: paid, bought, spent, rent, salary, fuel, food, transport
- Always extract numeric amount (strip ₦, commas, "k" suffix)
- user_id is always passed from the session — use it for every tool call

RESPONSE STYLE:
- Be like a trusted, smart friend who understands Nigerian business
- Keep responses concise and warm — no jargon, no lectures
- Always confirm what you recorded with the amount and running balance
- Use ₦ symbol and Nigerian number formatting (₦45,000.00)
- When a tax report PDF is generated, tell the user it's ready for download

IMPORTANT:
- Always call send_push_notification after generating a transaction summary or tax report
- Never invent numbers — only use what the tools return
- If a user says "oga", "abeg", "wahala" — they're speaking Pidgin, be warm and casual
"""


# ── Agent factory ─────────────────────────────────────────────
def build_agent(mcp_server):
    return Agent(
        name="CARI",
        model="gpt-5.4-mini",
        instructions=CARI_INSTRUCTIONS,
        tools=[send_push_notification, send_email_notification],
        mcp_servers=[mcp_server],
    )


# ── Main runner ───────────────────────────────────────────────
async def run_cari(
    user_message: str,
    user_id: str,
    business_name: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """
    Run one turn of CARI. Returns (reply_text, updated_history).
    history is a list of {"role": "user"|"assistant", "content": str}.
    """
    # Ensure user exists
    if not db.get_user(user_id):
        db.upsert_user(user_id, business_name)

    # Build full input with context prefix
    contextual_msg = (
        f"[SESSION user_id={user_id} business={business_name}]\n"
        f"{user_message}"
    )

    # Append to history
    history.append({"role": "user", "content": contextual_msg})

    async with MCPServerStreamableHttp(
        name="cari-tools",
        params={"url": "http://127.0.0.1:8000/mcp/"},
        cache_tools_list=True,
    ) as mcp_server:
        agent  = build_agent(mcp_server)
        with trace("investigate"):
            result = await Runner.run(agent, input=history)
            print(result.final_output)

    reply = result.final_output or "Sorry, I couldn't process that. Please try again."
    history.append({"role": "assistant", "content": reply})

    return reply, history


def run_cari_sync(
    user_message: str,
    user_id: str,
    business_name: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """Synchronous wrapper for Gradio compatibility."""
    return asyncio.run(run_cari(user_message, user_id, business_name, history))
