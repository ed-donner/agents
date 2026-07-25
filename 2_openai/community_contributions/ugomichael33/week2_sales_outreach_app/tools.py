from agents import function_tool

from config import RECIPIENT_EMAIL, SENDGRID_API_KEY, SENDER_EMAIL
from models import LeadContext

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
except Exception:
    sendgrid = None


@function_tool
def lookup_company(company: str) -> LeadContext:
    company = company.strip()
    return LeadContext(
        company=company,
        industry="B2B SaaS",
        pain_point="slow SOC2 audit prep and fragmented compliance evidence",
        value_prop="automate compliance evidence collection and accelerate audit readiness",
    )


def send_email_raw(
    to_email: str = "",
    subject: str = "",
    body: str = "",
    html_body: str | None = None,
) -> dict:
    to_email = (to_email or RECIPIENT_EMAIL or "").strip()

    if not to_email:
        return {"status": "skipped", "reason": "RECIPIENT_EMAIL not set"}

    if not (SENDGRID_API_KEY and SENDER_EMAIL and sendgrid):
        return {
            "status": "skipped",
            "reason": "SendGrid not configured or package missing",
            "to": to_email,
            "subject": subject,
        }

    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    content_type = "text/html" if html_body else "text/plain"
    content_value = html_body if html_body else body
    mail = Mail(
        Email(SENDER_EMAIL),
        To(to_email),
        subject,
        Content(content_type, content_value),
    )
    response = sg.send(mail)
    return {"status": response.status_code, "to": to_email, "subject": subject}


send_email = function_tool(send_email_raw)
