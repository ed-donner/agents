import os
import asyncio
import uuid
from dotenv import load_dotenv

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from agents import Agent, Runner, trace, function_tool

# =================================================
# Environment
# =================================================

load_dotenv(override=True)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = "dev.urvashicodes@gmail.com"  # test inbox

if not SENDGRID_API_KEY or not FROM_EMAIL:
    raise RuntimeError("Missing SENDGRID_API_KEY or FROM_EMAIL in .env")

sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# =================================================
# TOOL: Send Email (ONLY SIDE EFFECT)
# =================================================

@function_tool
def send_email(email_body: str, reply_to_address: str):
    """
    Sends exactly ONE email with a Reply-To address.
    """
    mail = Mail(
        from_email=Email(FROM_EMAIL),
        to_emails=To(TO_EMAIL),
        subject="ComplAI — quick intro",
        plain_text_content=Content("text/plain", email_body),
    )

    # Critical: Reply-To for inbound parsing
    mail.reply_to = Email(reply_to_address)

    sg.client.mail.send.post(request_body=mail.get())
    return {"status": "sent"}

# =================================================
# Drafting Agents (NO SIDE EFFECTS)
# =================================================

professional_agent = Agent(
    name="Professional Sales Agent",
    instructions=(
        "You are a professional sales agent for ComplAI, "
        "a SaaS platform that helps companies achieve SOC2 compliance. "
        "Write a serious, polished cold email."
    ),
    model="gpt-4o-mini",
)

engaging_agent = Agent(
    name="Engaging Sales Agent",
    instructions=(
        "You are a witty, engaging sales agent for ComplAI. "
        "Write a friendly, conversational cold email that feels human."
    ),
    model="gpt-4o-mini",
)

busy_agent = Agent(
    name="Busy Sales Agent",
    instructions=(
        "You are a very busy sales agent for ComplAI. "
        "Write a short, direct cold email with minimal fluff."
    ),
    model="gpt-4o-mini",
)

# Convert drafting agents into tools
professional_draft = professional_agent.as_tool(
    "professional_draft",
    "Generate a professional cold sales email",
)

engaging_draft = engaging_agent.as_tool(
    "engaging_draft",
    "Generate a witty, engaging cold sales email",
)

busy_draft = busy_agent.as_tool(
    "busy_draft",
    "Generate a short, direct cold sales email",
)

# =================================================
# Email Sender Agent (ONLY ONE ALLOWED TO SEND)
# =================================================

email_sender = Agent(
    name="Email Sender",
    instructions="""
You receive:
- email_body
- reply_to_address

Your job:
- Send EXACTLY ONE email using the send_email tool
- Use the provided reply_to_address unchanged
- Do not rewrite the email body
""",
    tools=[send_email],
    model="gpt-4o-mini",
)

# =================================================
# Sales Manager (THINKS + DECIDES + HANDOFF)
# =================================================

sales_manager = Agent(
    name="Sales Manager",
    instructions="""
You are a Sales Manager at ComplAI.

Steps:
1. Use ALL THREE draft tools to generate email drafts.
2. Compare them carefully.
3. Choose the single best email.
4. Hand off ONE payload containing:
   - email_body (the selected draft)
   - reply_to_address (provided by the user)

Rules:
- You must NOT write emails yourself.
- You must NOT send emails yourself.
- You must hand off EXACTLY ONE payload.
""",
    tools=[professional_draft, engaging_draft, busy_draft],
    handoffs=[email_sender],
    model="gpt-4o-mini",
)

# =================================================
# MAIN
# =================================================

async def main():
    # Unique lead identifier
    lead_id = f"lead_{uuid.uuid4().hex[:8]}"

    # MUST match SendGrid Inbound Parse host
    reply_to_address = f"{lead_id}@replies.urvashipatel.io"

    # Explicit payload so agents can pass it through cleanly
    message = f"""
Write a cold sales email addressed to Dear CEO.

Reply-To Address (IMPORTANT — pass through unchanged):
{reply_to_address}
"""

    with trace("Phase 1 — Agent Selection + Send"):
        await Runner.run(sales_manager, message)

    print("✅ Phase 1 complete")
    print("Lead ID:", lead_id)
    print("Reply-To:", reply_to_address)

if __name__ == "__main__":
    asyncio.run(main())
