from agents import function_tool
from sendgrid.helpers.mail import Mail, Email, To, Content
from schema import EmailStatus
from os import getenv
import sendgrid


@function_tool
def send_email(subject: str, html_body: str) -> dict[str, str]:
    """ Send out an email with the given subject and HTML body """
    try:
        sg = sendgrid.SendGridAPIClient(api_key=getenv('SENDGRID_API_KEY'))
        from_email = Email("from@example.com") # Change this to your verified email
        to_email = To("to@example.com") # Change this to your email
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        sg.client.mail.send.post(request_body=mail)
        return EmailStatus(subject=subject, status="success")
    except Exception as e:
        return EmailStatus(subject=subject, status="failed", error_message=str(e))
