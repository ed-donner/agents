import os
from dotenv import load_dotenv
import base64

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To, Attachment

from agents import Agent, function_tool

load_dotenv(override=True)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

@function_tool
def send_email(subject: str, email_body: str, to_email: str, resume_path: str) -> Dict[str, str]:
    """Send an email with the given subject, body and a resume attachment"""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email("hello@oluseun.dev")
    to_email = To(to_email)
    content = Content("text/html", email_body)
    attachment = Attachment(
        file_content=base64.b64encode(open(resume_path, "rb").read()).decode(),
        file_type="application/pdf",
        file_name=os.path.basename(resume_path),
    )
    mail = Mail(from_email, to_email, subject, content, attachments=[attachment]).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"

INSTRUCTIONS = """You are able to send a nicely formatted email based on a information in my resume.
You should use your tool to send one email, providing the information in the resume converted into clean, well presented email with an appropriate subject line.
"""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)