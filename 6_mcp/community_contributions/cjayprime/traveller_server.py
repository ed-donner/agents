from mcp.server.fastmcp import FastMCP
from typing import Literal
from traveller_types import BudgetPlan, HotelPlan, FlightPlan

TOTAL_SEARCHES_PER_TRAVEL_AGENT = 10
MODEL = "gpt-4o-mini"
SHARED_CONTEXT = {}
IS_FLIGHT_BOOKED = False

mcp = FastMCP("travel_architect")


@mcp.resource("traveller://travel_architect/{agent}")
def get_data(agent: Literal["flight", "hotel", "budget"]) -> dict:
    """
    Reads the previously saved trip data from the shared context.
    Args:
        agent: The agent data to read ('flight', 'hotel', or 'budget').
    """
    return SHARED_CONTEXT.get(agent, {})


@mcp.tool(name="book_flight", description="Books the flight for the user")
def book_flight():
    """
    This tool books the flight for the user
    """
    return "Successfully booked the full plan"


@mcp.tool(
    name="update_budget_breakdown",
    description="Saves the budget data to the shared context.",
)
def update_budget_breakdown(budget: BudgetPlan):
    """Saves the budget data"""
    SHARED_CONTEXT["budget"] = budget.model_dump()
    return "Budget data saved to memory.  Please hand off to the Itinerary Agent now."


@mcp.tool(
    name="update_hotel_breakdown",
    description="Saves the hotel data to the shared context.",
)
def update_hotel_breakdown(hotel: HotelPlan):
    """Saves the hotel data"""
    SHARED_CONTEXT["hotel"] = hotel.model_dump()
    return "Hotel data saved to memory.  Please hand off to the Budget Agent now."


@mcp.tool(
    name="update_flight_data",
    description="Saves the flight data to the shared context.",
)
def update_flight_data(flights: FlightPlan):
    """
    Saves the flight data to the shared context.
    """
    SHARED_CONTEXT["flight"] = flights.model_dump()
    return "Flight data saved to memory. Please hand off to the Hotel Agent now."


@mcp.tool(name="web_search", description="Performs a web search for the user")
def web_search():
    """
    This tool performs a web search for the user
    """
    return "Successfully performed a web search for the user"


if __name__ == "__main__":
    mcp.run(transport="stdio")
