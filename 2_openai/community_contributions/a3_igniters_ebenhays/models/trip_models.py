from typing import Optional
from pydantic import BaseModel, Field
from models.expense_models import Expense


class TravelContext(BaseModel):
    """
    Keeps track of the trip and expenses in the current conversation with the user.
    """

    trip_name: str = Field(default="My Trip", description="Active trip identifier")
    budget_usd: Optional[float] = Field(
        default=None, description="Trip budget in USD set by the user"
    )
    expenses: list[Expense] = Field(
        default_factory=list, description="All expenses logged in this session"
    )
    user_email: Optional[str] = Field(
        default=None, description="User's email address, saved when they mention it"
    )
