from agents import Agent
from core.email_sender import send_email

INSTRUCTIONS = """You are an email formatting and sending agent. You receive the body of a winning sales email.

Your job:
1. Convert the email body into clean, well-presented HTML with professional styling
2. Write an appropriate subject line
3. Use the send_email tool to send it

Keep the HTML simple and clean — no heavy frameworks, just inline CSS for readability."""

email_agent = Agent(
    name="Email Agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
