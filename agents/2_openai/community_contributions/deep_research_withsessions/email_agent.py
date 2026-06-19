import os
from typing import Dict
import smtplib
from email.mime.text import MIMEText
from agents import Agent, function_tool

@function_tool
def send_email(subject: str, html_body: str, email_address: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body to the user """

    # Your Gmail credentials
    gmail_user = os.getenv("FROM_EMAIL") 
    gmail_app_password = os.getenv("GOOGLE_APP_PW")
    to = email_address #os.getenv("TO_EMAIL") 

    if not all([gmail_user, gmail_app_password, to]):
        raise ValueError("Missing one or more required environment variables: FROM_EMAIL, GOOGLE_APP_PW, TO_EMAIL")

    # Create the email
    msg = MIMEText(html_body, "html")
    msg['Subject'] = subject or ""
    msg['From'] = gmail_user or ""
    msg['To'] = to or ""

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(gmail_user, gmail_app_password)
            server.send_message(msg)
        print('Email sent successfully!')
        return {"status": "success"}
    except Exception as e:
        print(f'Failed to send email: {e}')


#handoff prompt recommended by openai
RECOMMENDED_PROMPT_PREFIX = "# System context\nYou are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. \
Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when \
appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background;\
do not mention or draw attention to these transfers in your conversation with the user.\n"

INSTRUCTIONS = f"""{RECOMMENDED_PROMPT_PREFIX} You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report and the email address to which it should be sent. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    handoff_description="Convert a report to HTML and send it"
)
