from crewai.tools import BaseTool
from typing import Type, Dict
from pydantic import BaseModel, Field
import os
import resend


class EmailModel(BaseModel):
    """An email to be sent to the user"""
    # subject: str, html_body: str, email_to: str
    subject: str = Field(..., description="The subject of the email")
    html_body: str = Field(..., description="The HTML body of the email")
    email_to: str = Field(..., description="The recipient of the email")

class SendEmailTool(BaseTool):
    name: str = "The tool to send an email "
    description: str = (
        "Send an email to the recipient with the given subject and HTML body "
    )
    args_schema: Type[BaseModel] = EmailModel

    def _run(self, subject: str, html_body: str, email_to: str) -> Dict[str, str]:
        resend.api_key = os.environ.get('RESEND_API_KEY')
        params = {
            "from": "jimmy.chang@threecuptea.com",
            "to": [f"{email_to}"],
            "subject": subject,
            "html": html_body,
            "reply_to": "threecuptea@gmail.com"
        }
        
        response = resend.Emails.send(params)
        return {"status": "success", "id": response.get("id")}