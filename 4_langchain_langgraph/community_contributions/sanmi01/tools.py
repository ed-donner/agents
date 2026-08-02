import os
import requests
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv(override=True)

# Serper web search

serper = GoogleSerperAPIWrapper()

serper_tool = Tool(
    name="web_search",
    func=serper.run,
    description="Search the web for current agricultural product information, prices, and news."
)

# Wikipedia

wikipedia = WikipediaAPIWrapper()

wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

# Open-Meteo weather

@tool
def get_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather conditions for a location by coordinates.
    Returns temperature, precipitation, rain, and soil moisture.
    Use this to ground agricultural recommendations in real current conditions.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "precipitation",
            "rain",
            "soil_moisture_0_to_1cm",
            "relative_humidity_2m"
        ],
        "forecast_days": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        return {
            "temperature_c": current.get("temperature_2m"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "soil_moisture": current.get("soil_moisture_0_to_1cm"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "latitude": latitude,
            "longitude": longitude
        }
    except Exception as e:
        return {"error": str(e), "latitude": latitude, "longitude": longitude}


# Pushover notification

@tool
def send_push_notification(message: str) -> str:
    """
    Send a short push notification to the farmer via Pushover.
    Use this to deliver a one-line summary of the advisory report.
    """
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    url = "https://api.pushover.net/1/messages.json"

    if not token or not user:
        return "Pushover not configured -- set PUSHOVER_TOKEN and PUSHOVER_USER in .env"

    try:
        response = requests.post(
            url,
            data={"token": token, "user": user, "message": message},
            timeout=10
        )
        return f"Notification sent -- status {response.status_code}"
    except Exception as e:
        return f"Notification failed: {str(e)}"