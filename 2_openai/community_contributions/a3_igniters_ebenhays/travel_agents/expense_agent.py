from datetime import date
from typing import Optional
from agents import Agent, RunContextWrapper, function_tool
from models.expense_models import Expense, ExpenseCategory, ExpenseReport
from models.trip_models import TravelContext

EXPENSE_TRACKING_INSTRUCTIONS = """
You are an Expense Tracking Specialist for a Personal Travel & Expense Manager.

Your role is to help users record and review their travel expenses accurately.

Guidelines:
- Always use the log_expense tool to add expenses — never invent or assume amounts.
- After logging an expense, confirm it back to the user with the full details.
- When asked for a summary, call get_expense_summary and present results clearly
  with a category breakdown and remaining budget if set.
- Suggest setting a budget with set_trip_budget if none exists yet.
- Accepted categories: flight, hotel, food, transport, activities, other.
- Dates default to today if not specified by the user.
- Amounts must be in USD. Politely ask the user to convert if they give a
  foreign currency amount.
""".strip()


@function_tool
def log_expense(
    ctx: RunContextWrapper[TravelContext],
    category: str,
    amount_usd: float,
    description: str,
    expense_date: Optional[str] = None,
) -> str:
    """
    Log a new travel expense to the active trip.
    """
    try:
        expense_category = ExpenseCategory(category.lower())
    except ValueError:
        valid = ", ".join(c.value for c in ExpenseCategory)
        return f"Invalid category '{category}'. Please use one of: {valid}."

    if amount_usd <= 0:
        return "Expense amount must be greater than $0."
    if amount_usd > 50_000:
        return "Expense amount exceeds $50,000. Please verify the amount and try again."

    resolved_date = expense_date or date.today().isoformat()

    expense = Expense(
        category=expense_category,
        amount_usd=amount_usd,
        description=description,
        date=resolved_date,
        trip_name=ctx.context.trip_name,
    )
    ctx.context.expenses.append(expense)

    total = sum(e.amount_usd for e in ctx.context.expenses)
    budget_line = ""
    if ctx.context.budget_usd is not None:
        remaining = ctx.context.budget_usd - total
        status = "Over budget!" if remaining < 0 else f"${remaining:,.2f} remaining"
        budget_line = f"\n   Budget status: {status}"

    return (
        f"Expense logged!\n"
        f"   Category: {expense_category.value.title()}\n"
        f"   Amount: ${amount_usd:,.2f}\n"
        f"   Description: {description}\n"
        f"   Date: {resolved_date}\n"
        f"   Running total: ${total:,.2f}{budget_line}"
    )


@function_tool
def get_expense_summary(ctx: RunContextWrapper[TravelContext]) -> str:
    """
    Gives the user a full expense report for the active trip including category breakdown.
    """
    expenses = ctx.context.expenses
    trip_name = ctx.context.trip_name
    budget = ctx.context.budget_usd

    if not expenses:
        budget_info = (
            f"  Budget set: ${budget:,.2f}" if budget else "  No budget set yet."
        )
        return (
            f"No expenses logged for '{trip_name}' yet.\n{budget_info}\n"
            "Use log_expense to start tracking your spending."
        )

    report = ExpenseReport.generate_report(
        trip_name=trip_name,
        expenses=expenses,
        budget_usd=budget,
    )

    lines: list[str] = [
        f"Expense Report — {trip_name}",
        f"   Total expenses: {report.expense_count}",
        f"   Total spent: ${report.total_usd:,.2f}",
    ]

    if report.budget_usd is not None:
        status = "OVER BUDGET" if report.is_over_budget else "on track"
        lines.append(f"   Budget: ${report.budget_usd:,.2f}  ({status})")
        lines.append(f"   Remaining: ${report.remaining_usd:,.2f}")

    lines.append("\nBreakdown by Category:")
    for cat_name, total in sorted(
        report.breakdown_by_category.items(), key=lambda x: -x[1]
    ):
        pct = (total / report.total_usd * 100) if report.total_usd > 0 else 0
        lines.append(f"   {cat_name.title():<14} ${total:>9,.2f}  ({pct:.1f}%)")

    lines.append("\nAll Expenses:")
    for exp in sorted(report.expenses, key=lambda e: e.date):
        lines.append(
            f"   {exp.date}  {exp.category.value.title():<12} "
            f"${exp.amount_usd:>8,.2f}  {exp.description}"
        )

    return "\n".join(lines)


@function_tool
def set_trip_budget(
    ctx: RunContextWrapper[TravelContext],
    budget_usd: float,
) -> str:
    """
    Sets or updates the total budget for the active trip.
    """
    if budget_usd <= 0:
        return "Budget must be greater than $0."

    ctx.context.budget_usd = budget_usd
    total_spent = sum(e.amount_usd for e in ctx.context.expenses)
    remaining = budget_usd - total_spent
    status = (
        "Already over budget!"
        if remaining < 0
        else f"${remaining:,.2f} available to spend"
    )

    return (
        f"Budget set: ${budget_usd:,.2f} for '{ctx.context.trip_name}'\n"
        f"   Already spent: ${total_spent:,.2f}\n"
        f"   Status: {status}"
    )


expense_agent = Agent(
    name="ExpenseTrackerAgent",
    instructions=EXPENSE_TRACKING_INSTRUCTIONS,
    tools=[
        log_expense,
        get_expense_summary,
        set_trip_budget,
    ],
    model="gpt-4o-mini",
)
