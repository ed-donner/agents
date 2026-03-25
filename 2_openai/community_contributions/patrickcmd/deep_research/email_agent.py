import os
from typing import Dict

from agents import Agent, function_tool
import httpx
import logging
from dotenv import load_dotenv

load_dotenv(override=True)    
logger = logging.getLogger(__name__)


# ── Email configuration ────────────────────────────────────────────

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "you@yourverifieddomain.com")  # Change to your verified sender domain
MAIL_TO = os.environ.get("MAIL_TO", "example@example.com")        # Change to your recipient
SENDER_NAME = "AI Email Agent"
RESEND_API_URL = "https://api.resend.com/emails"
RESEND_REQUEST_TIMEOUT = 10.0

async def _send_via_resend(
    *,
    to: str,
    subject: str,
    text: str | None = None,
    html: str | None = None,
) -> dict:
    """Low-level async helper that posts to the Resend HTTP API."""
    payload: dict = {
        "from": f"{SENDER_NAME} <{MAIL_FROM}>",
        "to": [to],
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text

    async with httpx.AsyncClient(timeout=RESEND_REQUEST_TIMEOUT) as client:
        response = await client.post(
            RESEND_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        )

        if response.status_code == 401:
            logger.error("Resend auth failed — check RESEND_API_KEY")
            raise RuntimeError("Resend authentication failed")
        if response.status_code == 422:
            logger.error(f"Resend rejected request: {response.text}")
            raise RuntimeError(f"Resend validation error: {response.text}")
        if response.status_code == 429:
            logger.error("Resend rate limit hit (free tier: 100/day, 3000/month)")
            raise RuntimeError("Resend rate limit exceeded")

        response.raise_for_status()

    data = response.json()
    logger.info(f"Email sent to {to} — id: {data.get('id')}")
    return data


@function_tool
async def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email given the subject and HTML body """
    try:
        result = await _send_via_resend(
            to=MAIL_TO,
            subject=subject,
            html=html_body,
        )
        return {"status": "success", "id": result.get("id")}
    except Exception as e:
        logger.exception("Failed to send HTML email")
        return {"status": "error", "detail": str(e)}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4.1-mini",
)
