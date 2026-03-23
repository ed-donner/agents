import os
import resend
from agents import Agent, RunContextWrapper, function_tool

from models.expense_models import ExpenseReport
from models.trip_models import TravelContext

EMAIL_AGENT_INSTRUCTIONS = """
You are an Email Assistant for a Personal Travel & Expense Manager.
Your ONLY job is to compose and send the email immediately — no confirmations, no previews, no pauses.

Resolve recipient address:
  If ctx.context.user_email is set use it.
  if the user's message contains an email address call save_recipient_email,
  Ask ONCE for the address. The instant the user replies call save_recipient_email.

Gather content:
  If the request is about expenses, a budget, or a trip report call
    call get_expense_summary_for_email to get the data.
  Otherwise use the information already in the conversation.

Compose a well-formatted HTML email body.

Call send_email immediately. Do NOT ask for approval.

Reply to the user with a one-line confirmation that the email was sent.

Hard rules:
- NEVER ask "Should I send this?" or "Does this look good?" — just send it.
- NEVER ask for the address more than once.
- NEVER invent expense figures or trip data — only use what is provided.
""".strip()


@function_tool
def save_recipient_email(ctx: RunContextWrapper[TravelContext], email: str) -> str:
    """
    Persist the user's email address so it is reused automatically.
    Call this as soon as the user provides an address, then proceed to send immediately.
    """
    ctx.context.user_email = email
    return f"Address saved: {email}. Proceed immediately to compose and send the email."


@function_tool
def get_expense_summary_for_email(ctx: RunContextWrapper[TravelContext]) -> str:
    """
    Retrieve the current trip's expense data formatted for inclusion in an email.
    """
    expenses = ctx.context.expenses
    trip_name = ctx.context.trip_name
    budget = ctx.context.budget_usd

    if not expenses:
        return (
            f"No expenses have been logged for '{trip_name}' yet. "
            "Nothing to include in the email."
        )

    report = ExpenseReport.generate_report(
        trip_name=trip_name,
        expenses=expenses,
        budget_usd=budget,
    )

    lines: list[str] = [
        f"Trip: {trip_name}",
        f"Total expenses: {report.expense_count}",
        f"Total spent: ${report.total_usd:,.2f}",
    ]

    if report.budget_usd is not None:
        status = "OVER BUDGET" if report.is_over_budget else "on track"
        lines.append(f"Budget: ${report.budget_usd:,.2f} ({status})")
        lines.append(f"Remaining: ${report.remaining_usd:,.2f}")

    lines.append("\nBreakdown by Category:")
    for cat_name, total in sorted(
        report.breakdown_by_category.items(), key=lambda x: -x[1]
    ):
        pct = (total / report.total_usd * 100) if report.total_usd > 0 else 0
        lines.append(f"  {cat_name.title():<14} ${total:>9,.2f}  ({pct:.1f}%)")

    lines.append("\nAll Expenses:")
    for exp in sorted(report.expenses, key=lambda e: e.date):
        lines.append(
            f"  {exp.date}  {exp.category.value.title():<12} "
            f"${exp.amount_usd:>8,.2f}  {exp.description}"
        )

    return "\n".join(lines)


@function_tool
def send_email(
    ctx: RunContextWrapper[TravelContext],
    to: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an email via Resend.
    """
    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        return "RESEND_API_KEY is not set. Please add it to your .env file and restart."

    resend.api_key = resend_api_key
    from_address = os.getenv(
        "RESEND_FROM_EMAIL", "Travel Manager <onboarding@resend.dev>"
    )

    try:
        resend.Emails.send(
            {
                "from": from_address,
                "to": [to],
                "subject": subject,
                "html": body,
            }
        )
        return f"Email sent successfully to {to}"
    except Exception as exc:
        return f"Failed to send email: {type(exc).__name__}: {exc}"


email_agent = Agent(
    name="EmailAgent",
    instructions=EMAIL_AGENT_INSTRUCTIONS,
    tools=[save_recipient_email, get_expense_summary_for_email, send_email],
    model="gpt-4o-mini",
)
