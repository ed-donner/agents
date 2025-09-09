import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool, ModelSettings
from pydantic import BaseModel, Field

import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send an email with the given subject and HTML body """
    api_key=os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        return {'status': 'error', 'message': 'SENDGRID_API_KEY is missing'}
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email("adriana-salcedo@outlook.com")
        to_email = To("adri.salcedo@hotmail.de")
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        print("Email response", response.status_code)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

INSTRUCTIONS = """You will receive a finalized markdown report.
Convert the report into clean, HTML format.
You should use your tool to send one email.
Generate an appropriate email subject (8-12 words)."""

class EmailOut(BaseModel):
    subject: str
    body_html: str
    markdown_report: str

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    model_settings = ModelSettings(tool_choice = 'required'),
    output_type = EmailOut,
)