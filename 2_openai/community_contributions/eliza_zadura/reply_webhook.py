"""
Mailjet Reply Webhook Server

A FastAPI server that receives inbound email replies via Mailjet's Parse API
and uses an AI agent to generate and send contextual responses.

Usage:
    # Terminal 1: Start the webhook server
    uvicorn reply_webhook:app --port 8000

    # Terminal 2: Expose via ngrok
    ngrok http 8000

Then configure Mailjet Parse Route to POST to: https://<ngrok-url>/webhook/reply
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from mailjet_rest import Client
from agents import Agent, Runner, function_tool

# ----------------------------------
# Setup
# ----------------------------------

load_dotenv(override=True)

MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY")  # Your Mailjet keys
MAILJET_SECRET_KEY = os.environ.get("MAILJET_SECRET_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_NAME = os.environ.get("FROM_NAME")

app = FastAPI()


# ----------------------------------
# Tool: send reply email
# ----------------------------------


@function_tool
def send_reply(to_email: str, to_name: str, subject: str, body: str):
    """Send a reply email to the prospect."""
    mailjet = Client(
        auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY),
        version="v3.1",
    )
    data = {
        "Messages": [
            {
                "From": {"Email": FROM_EMAIL, "Name": FROM_NAME},
                "To": [{"Email": to_email, "Name": to_name}],
                "Subject": subject,
                "TextPart": body,
            }
        ]
    }
    response = mailjet.send.create(data=data)
    return {"status": "reply_sent", "status_code": response.status_code}


# ----------------------------------
# SDR Reply Agent
# ----------------------------------

reply_agent = Agent(
    name="SDR Reply Agent",
    instructions="""
You are an SDR (Sales Development Representative) continuing a sales conversation
for ComplAI, an AI-powered SaaS tool for SOC2 compliance.

Rules:
- Respond naturally to what the prospect wrote
- Ask ONE follow-up question to keep the conversation going
- If the prospect says they are not interested, politely thank them and disengage
- Keep replies under 120 words
- Be professional but friendly
- Always use the send_reply tool to send your response
""",
    tools=[send_reply],
    model="gpt-4o-mini",
)


# ----------------------------------
# Webhook endpoint
# ----------------------------------


@app.post("/webhook/reply")
async def receive_reply(request: Request):
    """
    Receives inbound email data from Mailjet Parse API.
    
    Mailjet sends form data with fields like:
    - From: sender email
    - Subject: email subject
    - Text-part: plain text body
    - Html-part: HTML body (if available)
    """
    form = await request.form()

    # Extract email details from Mailjet's Parse API payload
    prospect_email = form.get("From", "unknown@example.com")
    prospect_name = form.get("From", "Prospect").split("<")[0].strip()
    subject = form.get("Subject", "Re: ComplAI")
    message_text = form.get("Text-part", "") or form.get("Html-part", "")

    # Run the agent to craft and send a response
    await Runner.run(
        reply_agent,
        input=f"""
Inbound reply received from a sales prospect.

Prospect email: {prospect_email}
Prospect name: {prospect_name}
Subject: {subject}

Their message:
{message_text}

Craft a helpful, concise reply and send it using the send_reply tool.
Use "Re: {subject}" as the subject line.
"""
    )

    return {"status": "ok"}


# ----------------------------------
# Health check endpoint
# ----------------------------------


@app.get("/")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "running", "service": "Mailjet Reply Webhook"}
