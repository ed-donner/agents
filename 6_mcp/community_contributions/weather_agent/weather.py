from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("WEATHERAPI_API_KEY")

def fetch_weather_by_city(city: str):
    response = requests.get(f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=no")
    if response.status_code != 200:
        raise Exception(f"Failed to fetch weather for {city}")
    return response.json()

class Weather(BaseModel):

    @classmethod
    def get_temperature_by_city(cls, city: str):
        try:
            return {"success": True, "temperature_celsius": fetch_weather_by_city(city)["current"]["temp_c"]}
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch temperature for {city}: {e}"}
    
    @classmethod
    def get_weather_by_city(cls, city: str):
        try:
            return {"success": True, "weather": fetch_weather_by_city(city)["current"]["condition"]["text"]}    
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch weather for {city}: {e}"}
    
    @classmethod
    def get_humidity_by_city(cls, city: str):
        try:
            return {"success": True, "humidity": fetch_weather_by_city(city)["current"]["humidity"]} 
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch humidity for {city}: {e}"}
    
    @classmethod
    def get_wind_by_city(cls, city: str):
        try:
            return {"success": True, "wind_kph": fetch_weather_by_city(city)["current"]["wind_kph"]} 
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch wind for {city}: {e}"}