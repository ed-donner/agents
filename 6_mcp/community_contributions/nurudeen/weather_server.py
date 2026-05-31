import json
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather_server")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def _geocode(client: httpx.AsyncClient, name: str) -> dict[str, Any] | None:
    r = await client.get(GEOCODE_URL, params={"name": name.strip(), "count": 1})
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    return results[0] if results else None


@mcp.tool()
async def get_weather_for_location(location_name: str) -> str:
    """Current conditions and a 7-day outlook for a city, region, or country name.
    Use this for trip planning to understand typical conditions and seasonal patterns.
    """
    if not location_name or not location_name.strip():
        return json.dumps({"error": "location_name is required"})
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            place = await _geocode(client, location_name)
            if not place:
                return json.dumps(
                    {"error": f"Could not geocode {location_name!r}. Try a different spelling."}
                )

            lat, lon = place["latitude"], place["longitude"]
            label = place.get("name", location_name)
            country = place.get("country_code", "")

            fr = await client.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                    "timezone": "auto",
                    "forecast_days": 8,
                },
            )
            fr.raise_for_status()
            fc = fr.json()

            current = fc.get("current", {})
            daily = fc.get("daily", {})

            summary = {
                "resolved_location": f"{label}, {country}".strip(", "),
                "latitude": lat,
                "longitude": lon,
                "current": current,
                "daily_forecast": {
                    "time": daily.get("time", []),
                    "temperature_2m_max": daily.get("temperature_2m_max", []),
                    "temperature_2m_min": daily.get("temperature_2m_min", []),
                    "precipitation_sum": daily.get("precipitation_sum", []),
                    "weather_code": daily.get("weather_code", []),
                },
                "note": "Weather codes follow WMO; see Open-Meteo docs. Use with web research for best seasons to visit.",
            }
            return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Failed to get weather for {location_name}: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
