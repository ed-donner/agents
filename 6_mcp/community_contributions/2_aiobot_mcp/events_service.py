"""Ticketmaster event search service."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)


class EventsService:
    """Fetches events from Ticketmaster API."""

    def __init__(self):
        """Initialize EventsService with API key from environment."""
        self.api_key = os.getenv("TICKETMASTER_KEY")
        if not self.api_key:
            raise ValueError("TICKETMASTER_KEY environment variable is required")
        self.api_url = "https://app.ticketmaster.com/discovery/v2/events.json"

    async def search_events(
        self, city: str, country_code: str, keywords: list[str] | None = None, start_date: str | None = None
    ) -> list[dict] | dict:
        """Search for events on Ticketmaster.

        Args:
            city: City name
            country_code: ISO Alpha-2 country code (e.g., US, GB, CA)
            keywords: Optional list of search keywords
            start_date: Optional start date in ISO format (e.g., 2025-01-15T00:00:00Z)

        Returns:
            List of event dictionaries or error dict
        """
        params = {
            "apikey": self.api_key,
            "city": city,
            "countryCode": country_code,
            "size": 20,
        }

        if keywords:
            params["keyword"] = ",".join(keywords)
        if start_date:
            params["startDateTime"] = start_date

        try:
            logger.debug(f"Calling Ticketmaster API for {city}, {country_code}")
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                events = data.get("_embedded", {}).get("events", [])
                if not events:
                    logger.debug(f"No events found for {city}")
                    return []

                logger.debug(f"Found {len(events)} events for {city}")
                return [
                    {
                        "name": event["name"],
                        "date": event["dates"]["start"]["localDate"],
                        "venue": event["_embedded"]["venues"][0]["name"],
                        "url": event.get("url", "N/A"),
                    }
                    for event in events
                ]
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return {"error": str(e)}
