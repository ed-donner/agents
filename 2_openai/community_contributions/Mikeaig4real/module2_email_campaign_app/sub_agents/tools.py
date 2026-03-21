"""Tools for email campaign workflow."""

from typing import List, Dict
from agents import function_tool
from .schemas import ColdEmail, Contact, EmailPayload



def _render_email_logic(email: ColdEmail, recipient_name: str, company: str) -> str:
    """The actual rendering logic, safe to call from other functions."""
    return f"""
    <html>
      <body style='font-family: Arial, sans-serif; max-width: 680px;'>
        <p>Hi {recipient_name},</p>
        <p>{email.body_text}</p>
        <p><strong>{email.cta}</strong></p>
        <p>Best,<br/>ComplAI Team</p>
        <hr/>
        <small>For {company} | Preview: {email.preview_text}</small>
      </body>
    </html>
    """.strip()


@function_tool
def get_target_contacts(segment: str = "soc2_readiness") -> List[Dict[str, str]]:
    """Return a small target contact list."""
    data = {
        "soc2_readiness": [
            {"name": "Head of Engineering", "email": "eng-lead@example.com", "company": "Northwind"},
            {"name": "VP Security", "email": "security-vp@example.com", "company": "Contoso"},
            {"name": "Compliance Director", "email": "compliance@example.com", "company": "Fabrikam"},
        ]
    }
    return data.get(segment, [])


@function_tool
def render_html_email(email: ColdEmail, recipient_name: str, company: str) -> str:
    """Render HTML from structured fields."""
    return _render_email_logic(email, recipient_name, company)


@function_tool
def build_mail_merge_plan(email: ColdEmail, contacts: List[Contact]) -> List[Dict[str, str]]:
    """Build recipient-specific payloads."""
    plan = []
    for contact in contacts:
        plan.append(EmailPayload(
            to=contact.email,
            subject=email.subject,
            html=_render_email_logic(email, contact.name, contact.company)
        ))
    return plan


@function_tool
def send_mail_merge_dry_run(payloads: List[EmailPayload]) -> Dict[str, str | int]:
    """Dry run send operation."""
    # My sendgrid is unavailable atm
    return {"status": "dry_run_ok", "emails_prepared": len(payloads), "payloads": payloads}