from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER__API_KEY")

def retrieve_city_weather(city: str):
    response = requests.get(f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no")
    if response.status_code != 200:
        raise Exception(f"Weather for {city} failed to fetch")
    return response.json()

class Atmosphere(BaseModel):

    @classmethod
    def fetch_temperature(cls, city: str):
        try:
            return {"success": True, "temperature_celsius": retrieve_city_weather(city)["current"]["temp_c"]}
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch temperature for {city}: {e}"}

    @classmethod
    def fetch_condition(cls, city: str):
        try:
            return {"success": True, "weather": retrieve_city_weather(city)["current"]["condition"]["text"]}
        except Exception as e:
            return {"success": False, "error": f"Did not fetch weather for {city}: {e} succesfully"}

    @classmethod
    def fetch_humidity(cls, city: str):
        try:
            return {"success": True, "humidity": retrieve_city_weather(city)["current"]["humidity"]}
        except Exception as e:
            return {"success": False, "error": f"Did not fetch humidity for {city}: {e} succesfully"}

    @classmethod
    def fetch_wind_speed(cls, city: str):
        try:
            return {"success": True, "wind_kph": retrieve_city_weather(city)["current"]["wind_kph"]}
        except Exception as e:
            return {"success": False, "error": f"Did notfetch wind for {city}: {e} succesfully"}
