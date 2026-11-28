import resend
import html
from agents import function_tool
from config import RESEND_API_KEY,EMAIL_ADDRESS,USER_NAME

resend.api_key = RESEND_API_KEY

def send_email(subject,html_body) -> str:
    escaped_body = html.escape(html_body)
    html_body = escaped_body.replace("\n", "<br>\n")
    params = {
        "from": f"{USER_NAME} <onboarding@resend.dev>",
        "to" : [EMAIL_ADDRESS],
        "subject": subject,
        "html": f"<html><body><p>{html_body}</p></body></html>",
    }
    resend.Emails.send(params)
    return "Email sent successfully!"


@function_tool
def send_email_tool(subject : str,html_body : str) -> str:
    """
    Send an email using the Resend API.

    Args:
        subject: Subject of the selected email.
        body: Plain-text body of the selected email.
    """
    response = send_email(subject,html_body);
    return response
