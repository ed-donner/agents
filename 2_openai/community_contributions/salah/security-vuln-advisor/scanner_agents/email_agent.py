import os
import logging
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, Runner, function_tool

logger = logging.getLogger(__name__)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(os.environ.get("EMAIL_FROM"))
    to_email = To(os.environ.get("EMAIL_TO"))
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    logger.info(f"Email sent, status code: {response.status_code}")
    return {"status": "success", "status_code": str(response.status_code)}


class EmailAgent:
    """Agent that sends security report via email using SendGrid."""

    INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a security report.
You will be provided with a detailed security report in markdown format. You should use your tool to send one email,
providing the report converted into clean, well presented HTML with an appropriate subject line that includes
the image name and risk level."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = self._create_agent()
        logger.info("EmailAgent initialized")

    def _create_agent(self) -> Agent:
        """Create the email agent with send_email tool."""
        return Agent(
            name="EmailAgent",
            instructions=self.INSTRUCTIONS,
            tools=[send_email],
            model=self.model,
        )

    async def send_report(self, markdown_report: str) -> Dict[str, str]:
        """
        Send security report via email.

        Args:
            markdown_report: Markdown formatted security report

        Returns:
            Dict with status information
        """
        logger.info("Sending security report via email")

        try:
            result = await Runner.run(self.agent, markdown_report)
            logger.info("Email sent successfully")
            return result.final_output
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
