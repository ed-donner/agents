from typing import Dict
from agents import Agent, function_tool, ModelSettings
from dotenv import load_dotenv
import os
import sendgrid
from sendgrid.helpers.mail import Mail
from constants import default_model
import asyncio

load_dotenv(override=True)

email = os.environ.get("EMAIL_ACCOUNT")


@function_tool
async def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
  """ Send out an email with the given subject and HTML body to all sales prospects """
  try:
    sendgrid_client = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    message = Mail(from_email=email, to_emails=email, subject=subject, html_content=html_body)
    response = sendgrid_client.send(message)
    if response.status_code == 202:
      return {"status": "success"}
  except Exception as e:
    print(e.message)
    return e

subject_writer_instructions = f"You can write a relevant subject for an email to be sent, you are given a message and you need to write a subject for that message."
subject_writer_agent = Agent("Email Subject Writer", instructions=subject_writer_instructions, model=default_model)
subject_writer_tool = subject_writer_agent.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

email_formatter_instructions = f"You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design which will attract customers."
email_formatter_agent = Agent("Email HTML formatter", instructions=email_formatter_instructions, model=default_model)
email_formatter_tool = email_formatter_agent.as_tool(tool_name="email_formatter", tool_description="Convert a text email body to an HTML email body")

email_manager_instructions = f"You are an Email Manager, you act as an email formatter and sender. You receive the body of an email to be sent. \
You first use the subject_writer tool to write a subject for the email, then use the email_formatter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject and HTML body."

email_manager_tools = [subject_writer_tool, email_formatter_tool, send_html_email]
email_manager = Agent("Email Manager", instructions=email_manager_instructions, model=default_model, tools=email_manager_tools, handoff_description="Convert an email to HTML and send it",model_settings=ModelSettings(tool_choice="required"))
