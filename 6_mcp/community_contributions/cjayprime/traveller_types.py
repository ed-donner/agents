from pydantic import BaseModel, Field
from typing import List


class Activity(BaseModel):
    time_of_day: str = Field(description="e.g., '09:00 AM' or 'Evening'")
    description: str = Field(description="The specific activity or transit step")
    location: str = Field(description="Where this activity will take place")
    cost_estimate: float = Field(
        description="Estimated cost for this specific activity"
    )


class DayPlan(BaseModel):
    day_number: int = Field(description="The sequential day of the trip (1, 2, 3...)")
    theme: str = Field(
        description="A brief title for the day (e.g., 'Exploring Old Tokyo')"
    )
    activities: List[Activity] = Field(
        description="List of scheduled events for the day"
    )


class ItineraryPlan(BaseModel):
    trip_title: str = Field(description="A catchy name for the trip")
    daily_schedule: List[DayPlan] = Field(description="The full day-by-day breakdown")
    breakdown: str = Field(
        description="The agent's reasoning about the pace and flow of the trip. Use no less than 3 paragraphs to describe the trip and daily schedule."
    )


class MultiItinerary(BaseModel):
    options: List[ItineraryPlan] = Field(
        description="5 different trip versions/itinerary plans"
    )
    reasons: str = Field(description="Why these 5 specific variations were chosen")


class CostBreakdown(BaseModel):
    category: str = Field(description="e.g., 'Flights', 'Hotels', 'Food', 'Activities'")
    estimated_cost: float = Field(description="The price in USD")
    notes: str = Field(description="Brief justification for this cost")


class BudgetPlan(BaseModel):
    total_estimated_budget: float = Field(description="The sum of all costs")
    is_within_limit: bool = Field(
        description="Whether this fits the user's specified budget"
    )
    breakdown: list[CostBreakdown] = Field(description="Detailed list of expenses")
    saving_tips: str = Field(
        description="Advice on how to lower the cost of this specific trip"
    )


class Hotel(BaseModel):
    name: str = Field(description="The full name of the hotel or accommodation")
    location: str = Field(description="The neighborhood or specific address")
    price_per_night: float = Field(description="Nightly rate in USD")
    total_price: float = Field(description="Total cost for the entire stay")
    rating: float = Field(description="User rating (e.g., 4.5/5.0)")
    amenities: List[str] = Field(
        description="List of key features (e.g., 'Free WiFi', 'Pool')"
    )
    decision_reason: str = Field(
        description="Why this hotel is a good fit for the user's request"
    )


class HotelPlan(BaseModel):
    options: List[Hotel] = Field(description="A list of 3-5 hotel options found")
    search_summary: str = Field(
        description="A summary of the local hotel market for these dates"
    )


class FlightWebSearchItem(BaseModel):
    query: str = Field(
        description="The specific search term used (e.g., 'Direct flights NYC to LON June 15')"
    )
    airline: str = Field(description="The name of the airline found")
    price: float = Field(description="The price of the flight in USD (numerical only)")
    duration: str = Field(description="The total travel time (e.g., '7h 30m')")
    stops: int = Field(description="Number of layovers (0 for direct)")


class FlightPlan(BaseModel):
    searches: List[FlightWebSearchItem] = Field(
        description="A list of specific flight options found via web search."
    )


class InputGuardrail(BaseModel):
    in_appropriate: bool = Field(description="Whether the question is inappropriate")
    description: str = Field(
        description="The message to redirect the user. It should inform the user of your inability to continue if the input prompt is inappropriate"
    )


class OutputGuardrail(BaseModel):
    in_appropriate: bool = Field(
        description="Whether the agent's response fails quality or safety checks"
    )
    correction_needed: bool = Field(
        description="True if the response needs to be regenerated"
    )
    failure_reason: str = Field(
        description="Internal reason for the failure (e.g., 'Insufficient options provided')"
    )
    description: str = Field(
        description="A polite message to the user if the system cannot provide the output"
    )
