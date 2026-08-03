import os
from typing import Dict
from openai import AsyncOpenAI
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool, OpenAIChatCompletionsModel


@function_tool
def send_email(subject: str, html_body: str, recipient_email: str) -> Dict[str, str]:
    """Send an email with the given subject, HTML body, and recipient email address"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("srivastavaaryan608@gmail.com")  # put your verified sender here
    to_email = To(recipient_email)  # use the dynamic recipient
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report and the recipient email. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line, to the specified recipient email."""

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash-lite",
    openai_client=AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ.get("GEMINI_API_KEY"),
    ),
)

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=gemini_model,
)
