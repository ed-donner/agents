import os
import re
from typing import Dict

import requests
from agents import Agent, function_tool

@function_tool
def send_research_notification(report_content: str) -> Dict[str, str]:
    """ Send a research report as a Pushover notification """
    url = "https://api.pushover.net/1/messages.json"
    
    # Clean up markdown and HTML for better readability in notifications
    clean_content = re.sub(r'<[^>]+>', '', report_content)  # Remove HTML tags
    clean_content = re.sub(r'#{1,6}\s*', '', clean_content)  # Remove markdown headers
    clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)  # Remove bold markdown
    clean_content = re.sub(r'\*(.*?)\*', r'\1', clean_content)  # Remove italic markdown
    clean_content = re.sub(r'\n\n+', '\n\n', clean_content)  # Clean multiple newlines
    
    # Truncate if too long for Pushover (max 1024 chars)
    if len(clean_content) > 900:
        clean_content = clean_content[:900] + "...\n\n[Report truncated - see full version in trace]"
    
    data = {
        "token": os.environ.get('PUSHOVER_TOKEN'),
        "user": os.environ.get('PUSHOVER_USER'),
        "message": clean_content,
        "title": "Research Report Complete"
    }
    
    response = requests.post(url, data=data)
    print("Notification response", response.status_code)
    if response.status_code == 200:
        return {"status": "success", "message": "Research report notification sent successfully"}
    else:
        return {"status": "error", "message": f"Error {response.status_code}: {response.text}"}

INSTRUCTIONS = """You are able to send a research report notification via Pushover.
You will be provided with a detailed markdown report. You should use your tool to send one notification 
with the report content. The notification should be clean and readable."""

notification_agent = Agent(
    name="Notification agent",
    instructions=INSTRUCTIONS,
    tools=[send_research_notification],
    model="gpt-4o-mini",
)
