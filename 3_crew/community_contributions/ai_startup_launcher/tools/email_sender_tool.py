import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(filename="logs/email_logs.txt", level=logging.INFO)

class EmailSenderInput(BaseModel):
    recipient_email: str = Field(..., description="Investor email")
    subject: str = Field(..., description="Email subject")
    message: str = Field(..., description="Email message body")


class EmailSenderTool(BaseTool):
    name: str = "Email Sender Tool"
    description: str = "Sends outreach emails to investors."
    args_schema: Type[BaseModel] = EmailSenderInput

    def _run(self, recipient_email: str, subject: str, message: str) -> str:
        try:
            sender_email = os.environ.get("EMAIL")
            app_password = os.environ.get("APP_PASSWORD")

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=60)
            server.ehlo()
            server.starttls()
            server.login(sender_email, app_password)

            server.sendmail(sender_email, recipient_email, msg.as_string())
            server.quit()

            logging.info(f"Email sent to {recipient_email}")
            return f"Email successfully sent to {recipient_email}"

        except Exception as e:
            logging.error(str(e))
            return f"Failed to send email: {str(e)}"