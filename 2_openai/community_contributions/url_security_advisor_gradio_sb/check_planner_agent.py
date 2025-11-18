from pydantic import BaseModel, Field
from agents import Agent
from guardrail_agent import guardrail_against_data

HOW_MANY_CHECKS = 3

INSTRUCTIONS = f"""
You are a cybersecurity analysis planner. 
Given a URL, decide on {HOW_MANY_CHECKS} specific security aspects or investigation points 
that should be checked to determine if the URL is safe or dangerous. 
For each check, explain why this aspect is important.

Example aspects include:
- SSL/TLS and HTTPS validity
- Phishing or impersonation risk
- Redirects or obfuscated domain structure
- Malware or malicious content
- Domain reputation or age
- Suspicious query parameters

Return exactly {HOW_MANY_CHECKS} items describing what to check and why.
"""

class UrlCheckItem(BaseModel):
    """A single security aspect to investigate for the given URL."""
    reason: str = Field(description="Your reasoning for why this check is important for determining the URL's safety.")
    check: str = Field(description="The specific aspect to analyze (e.g., SSL validity, phishing risk, redirect behavior).")
class UrlCheckPlan(BaseModel):
    """A structured plan of URL safety checks to perform."""
    checks:list[UrlCheckItem] = Field(description="A list of security aspects to analyze for this URL.")

check_planner_agent = Agent(
    name="URLPlannerAgent", 
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=UrlCheckPlan,
    input_guardrails=[guardrail_against_data]
)