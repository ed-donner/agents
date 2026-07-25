import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExpenseCategory(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    FOOD = "food"
    TRANSPORT = "transport"
    ACTIVITIES = "activities"
    OTHER = "other"


class Expense(BaseModel):
    """This logs your expenses for a trip."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this expense entry",
    )
    category: ExpenseCategory = Field(description="Category this expense belongs to")
    amount_usd: float = Field(gt=0, description="Amount spent in USD")
    description: str = Field(description="Short description of the expense")
    date: str = Field(description="Date of the expense in YYYY-MM-DD format")
    trip_name: str = Field(description="Name or identifier of the trip this belongs to")
    notes: Optional[str] = Field(default=None, description="Optional additional notes")

    @field_validator("amount_usd")
    @classmethod
    def validate_reasonable_amount(cls, expense_amount: float) -> float:
        if expense_amount > 50_000:
            raise ValueError(
                "Expense amount exceeds $50,000 — please verify the value."
            )
        return round(expense_amount, 2)


class ExpenseReport(BaseModel):
    """This returns an aggregated expense summary for a trip."""

    trip_name: str = Field(description="Name or identifier of the trip")
    expenses: list[Expense] = Field(
        default_factory=list, description="All expenses logged for this trip"
    )
    total_usd: float = Field(
        default=0.0,
        description="This returns the total amount spent across all expenses",
    )
    breakdown_by_category: dict[str, float] = Field(
        default_factory=dict,
        description="This returns the spending totals keyed by category name",
    )
    budget_usd: Optional[float] = Field(
        default=None, description="Total budget set for this trip in USD"
    )
    remaining_usd: Optional[float] = Field(
        default=None,
        description="Remaining budget (budget - total spent); None if no budget set",
    )
    is_over_budget: bool = Field(
        default=False,
        description="True when spending has exceeded the set budget",
    )
    expense_count: int = Field(default=0, description="Total number of expense entries")

    @classmethod
    def generate_report(
        cls, trip_name: str, expenses: list[Expense], budget_usd: Optional[float] = None
    ) -> "ExpenseReport":
        """Generates a report from a list of expenses."""
        total = round(sum(e.amount_usd for e in expenses), 2)
        breakdown: dict[str, float] = {}
        for expense in expenses:
            key = expense.category.value
            breakdown[key] = round(breakdown.get(key, 0.0) + expense.amount_usd, 2)

        remaining = round(budget_usd - total, 2) if budget_usd is not None else None
        over_budget = (remaining is not None) and (remaining < 0)

        return cls(
            trip_name=trip_name,
            expenses=expenses,
            total_usd=total,
            breakdown_by_category=breakdown,
            budget_usd=budget_usd,
            remaining_usd=remaining,
            is_over_budget=over_budget,
            expense_count=len(expenses),
        )
