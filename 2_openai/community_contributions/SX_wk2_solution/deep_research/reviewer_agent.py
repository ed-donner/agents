from agents import Agent
from email_agent import email_agent

# Note there is NO writer_agent - reviewer_agent loop to keep it simple
REVIEWER_INSTRUCTIONS = """
You are a professional research report writer.
Review the draft research report given to you.

If acceptable:
APPROVED

Then handoff to the email agent.

If not acceptable:
Rewrite the report then handoff to the email agent.
"""


# Hands off to email agent
reviewer_agent = Agent(
    name="Reviewer Agent",
    instructions=REVIEWER_INSTRUCTIONS,
    model="gpt-4o-mini",
    handoffs=[email_agent],
)