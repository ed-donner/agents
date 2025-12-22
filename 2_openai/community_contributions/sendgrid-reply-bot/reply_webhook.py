import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from agents import Agent, Runner, function_tool

# ----------------------------------
# Setup
# ----------------------------------

load_dotenv(override=True)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")

sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

app = FastAPI()

# ----------------------------------
# Tool: send reply email (side effect)
# ----------------------------------

@function_tool
def send_reply(to_email: str, subject: str, body: str):
    """Send a single reply email to the prospect."""
    mail = Mail(
        from_email=Email(FROM_EMAIL),
        to_emails=To(to_email),
        subject=subject,
        plain_text_content=Content("text/plain", body),
    )
    sg.client.mail.send.post(request_body=mail.get())
    return {"status": "reply_sent"}

# ----------------------------------
# SDR Reply Agent
# ----------------------------------

reply_agent = Agent(
    name="SDR Reply Agent",
    instructions="""
You are an SDR continuing a sales conversation.

Rules:
- Respond naturally to what the prospect wrote
- Ask ONE follow-up question
- If the prospect says they are not interested, politely disengage
- Keep replies under 120 words
""",
    tools=[send_reply],
    model="gpt-4o-mini",
)

# ----------------------------------
# Webhook endpoint
# ----------------------------------

@app.post("/webhooks/sendgrid/reply")
async def receive_reply(request: Request):
    form = await request.form()

    prospect_email = form.get("from")
    original_subject = form.get("subject", "Re: ComplAI — quick intro")
    message_text = form.get("text")

    await Runner.run(
        reply_agent,
        input=f"""
Inbound reply received.

Prospect email:
{prospect_email}

Original subject:
{original_subject}

Message:
{message_text}

Write a concise, helpful reply and send it using the send_reply tool.
"""
    )

    return {"status": "ok"}
