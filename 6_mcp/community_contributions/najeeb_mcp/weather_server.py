"""MCP (stdio): local process, remote API — Open-Meteo (free, no API key)."""

from __future__ import annotations

import json
from urllib.parse import quote
from urllib.request import urlopen

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server_open_meteo")

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"


def _http_get_json(url: str, timeout: float = 15.0) -> dict:
    with urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


@mcp.tool()
async def weather_for_city(city: str) -> str:
    """Current weather summary for a city using Open-Meteo (free, no API key).

    Args:
        city: City name, e.g. 'Paris' or 'Tokyo'.
    """
    q = quote(city.strip())
    geo = _http_get_json(f"{GEOCODE}?name={q}&count=1&language=en&format=json")
    results = geo.get("results") or []
    if not results:
        return f"No geocoding match for {city!r}. Try another spelling."

    loc = results[0]
    lat, lon = loc["latitude"], loc["longitude"]
    name = loc.get("name", city)
    country = loc.get("country", "")

    wx = _http_get_json(
        f"{FORECAST}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        "&timezone=auto"
    )
    cur = wx.get("current") or {}
    temp = cur.get("temperature_2m")
    hum = cur.get("relative_humidity_2m")
    code = cur.get("weather_code")
    wind = cur.get("wind_speed_10m")

    return (
        f"{name}, {country} ({lat:.2f}, {lon:.2f})\n"
        f"Temperature: {temp} °C\n"
        f"Relative humidity: {hum} %\n"
        f"Wind (10m): {wind} km/h\n"
        f"Weather code (WMO): {code}\n"
        "(Data: Open-Meteo, no API key required.)"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
