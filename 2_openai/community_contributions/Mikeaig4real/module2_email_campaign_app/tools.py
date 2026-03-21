"""Tools for email campaign workflow."""

from typing import List
from agents import function_tool

from schemas import ColdEmail, Contact, EmailPayload
from debug import debug_print


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
def get_target_contacts(segment: str = "soc2_readiness") -> List[Contact]:
    """Return a small target contact list."""
    debug_print(f"DEBUG: get_target_contacts called for segment: {segment}")
    data = {
        "soc2_readiness": [
            {
                "name": "Head of Engineering",
                "email": "eng-lead@example.com",
                "company": "Northwind",
            },
            {
                "name": "VP Security",
                "email": "security-vp@example.com",
                "company": "Contoso",
            },
            {
                "name": "Compliance Director",
                "email": "compliance@example.com",
                "company": "Fabrikam",
            },
        ]
    }
    contacts = data.get(segment, [])
    debug_print(f"DEBUG: Found {len(contacts)} contacts: {contacts}")
    return contacts


@function_tool
def render_html_email(email: ColdEmail, recipient_name: str, company: str) -> str:
    """Render HTML from structured fields."""
    debug_print(f"DEBUG: render_html_email called for {recipient_name} at {company}")
    return _render_email_logic(email, recipient_name, company)


@function_tool
def build_mail_merge_plan(
    email: ColdEmail, contacts: List[Contact]
) -> List[EmailPayload]:
    """Build recipient-specific payloads."""
    debug_print(f"DEBUG: build_mail_merge_plan started for {len(contacts)} contacts...")
    debug_print(f"DEBUG: Using email subject: {email.subject}")
    plan = []
    for contact in contacts:
        payload = EmailPayload(
            to=contact.email,
            subject=email.subject,
            html=_render_email_logic(email, contact.name, contact.company),
        )
        plan.append(payload)
        debug_print(f"DEBUG: Built payload for {contact.email}")

    debug_print(f"DEBUG: Successfully built {len(plan)} payloads.")
    return plan


@function_tool
def send_mail_merge_dry_run(payloads: List[EmailPayload]) -> str:
    """Dry run send operation that returns a formatted report."""
    debug_print(f"DEBUG: send_mail_merge_dry_run called with {len(payloads)} payloads.")

    report = f"### Dry Run Complete: {len(payloads)} Emails Prepared\n\n"
    for i, p in enumerate(payloads):
        report += f"**Recipient {i + 1}:** {p.to}\n"
        report += f"**Subject:** {p.subject}\n"
        report += f"**Content Preview:** {p.html[:150].strip()}...\n"
        report += "---\n\n"

        print(f"DEBUG: Payload {i + 1} to {p.to}:")
        print(f"DEBUG:   Subject: {p.subject}")

    # My sendgrid is unavailable atm
    debug_print("DEBUG: Successfully generated dry-run report.")
    return report
