from travel import TravelerProfile, get_activities, get_hotels
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("travel_server")


@mcp.tool()
async def search_hotels(destination: str, max_nightly_rate: float = 1000.0) -> list[dict]:
    """Search hotels in the destination that fit within the nightly budget."""
    hotels = [
        hotel.model_dump()
        for hotel in get_hotels(destination)
        if hotel.nightly_rate <= max_nightly_rate
    ]
    return sorted(hotels, key=lambda hotel: hotel["nightly_rate"])


@mcp.tool()
async def search_activities(destination: str, category: str = "") -> list[dict]:
    """Search activities in the destination, optionally filtering by category."""
    activities = [activity.model_dump() for activity in get_activities(destination)]
    if category:
        activities = [
            activity
            for activity in activities
            if activity["category"].lower() == category.lower()
        ]
    return activities


@mcp.tool()
async def save_itinerary(name: str, title: str, summary: str) -> str:
    """Save the itinerary title and overview for the traveler."""
    traveler = TravelerProfile.get(name)
    return traveler.save_itinerary(title, summary)


@mcp.tool()
async def add_itinerary_item(
    name: str,
    day: int,
    time: str,
    title: str,
    location: str,
    cost: float,
    notes: str,
) -> str:
    """Add a scheduled itinerary item for the traveler."""
    traveler = TravelerProfile.get(name)
    return traveler.add_itinerary_item(day, time, title, location, cost, notes)


@mcp.tool()
async def book_hotel(name: str, hotel_name: str, nights: int) -> str:
    """Book a hotel stay from the local travel catalog."""
    traveler = TravelerProfile.get(name)
    hotels = get_hotels(traveler.destination)
    hotel = next((hotel for hotel in hotels if hotel.name == hotel_name), None)
    if not hotel:
        raise ValueError(f"Hotel '{hotel_name}' was not found in {traveler.destination}.")
    total_cost = hotel.nightly_rate * nights
    details = f"{nights} nights in {hotel.area} at ${hotel.nightly_rate:.2f} per night."
    return traveler.add_booking("hotel", hotel.name, traveler.destination, total_cost, details)


@mcp.tool()
async def book_activity(name: str, activity_name: str) -> str:
    """Book an activity from the local travel catalog."""
    traveler = TravelerProfile.get(name)
    activities = get_activities(traveler.destination)
    activity = next((activity for activity in activities if activity.name == activity_name), None)
    if not activity:
        raise ValueError(
            f"Activity '{activity_name}' was not found in {traveler.destination}."
        )
    details = f"{activity.category.title()} activity in {activity.area} lasting {activity.duration_hours} hours."
    return traveler.add_booking(
        "activity",
        activity.name,
        traveler.destination,
        activity.price,
        details,
    )


@mcp.resource("travel://profile/{name}")
async def read_profile_resource(name: str) -> str:
    traveler = TravelerProfile.get(name)
    return traveler.profile_report()


@mcp.resource("travel://preferences/{name}")
async def read_preferences_resource(name: str) -> str:
    traveler = TravelerProfile.get(name)
    return traveler.preferences_report()


@mcp.resource("travel://itinerary/{name}")
async def read_itinerary_resource(name: str) -> str:
    traveler = TravelerProfile.get(name)
    return traveler.itinerary_report()


if __name__ == "__main__":
    mcp.run(transport="stdio")
