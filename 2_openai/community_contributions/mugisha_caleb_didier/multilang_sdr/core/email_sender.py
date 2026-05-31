import os

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import function_tool


@function_tool
def send_email(subject: str, html_body: str) -> dict[str, str]:
    """Send an email with the given subject and HTML body to the sales prospect."""
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
    from_email = Email(os.getenv("SENDER_EMAIL"))
    to_email = To(os.getenv("RECIPIENT_EMAIL"))
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return {"status": "success", "status_code": str(response.status_code)}
