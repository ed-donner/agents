import os
# import sendgrid
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

# Define the input schema for the tool
class SendEmailInput(BaseModel):
    """A message to be sent to the user"""
    to_email: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject line.")
    content: str = Field(..., description="Email body content.")


class SendGridTool(BaseTool):
    name: str = "Send Email via SendGrid"
    description: str = (
        "Useful for sending an email to a specified recipient using the SendGrid API. "
    )
    args_schema: type[BaseModel] = SendEmailInput

    def _run(self, to_email: str, subject: str, content: str) -> str:
        """The logic for sending the email."""
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            mail = Mail(
                from_email=os.environ["SENDGRID_FROM_EMAIL"],
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            response = sg.send(mail)
            if response.status_code == 202:
                return f"Email sent successfully to {to_email}. Status code: {response.status_code}"
            else:
                return f"Failed to send email. Status code: {response.status_code}, body: {response.body}"
        except Exception as e:
            return f"An error occurred: {str(e)}"
