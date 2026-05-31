"""
Weather Researcher - Helper functions for fetching weather data from Stormglass API.
Stormglass provides comprehensive weather forecasts including marine weather data.
"""
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Stormglass API configuration
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")
STORMGLASS_BASE_URL = "https://api.stormglass.io/v2"

# Check if API key is available
STORMGLASS_AVAILABLE = bool(STORMGLASS_API_KEY)


def _make_request(endpoint: str, params: Dict) -> Optional[Dict]:
    """Make a request to Stormglass API with error handling."""
    if not STORMGLASS_AVAILABLE:
        return {"error": "STORMGLASS_API_KEY not found in environment variables"}
    
    try:
        headers = {
            "Authorization": STORMGLASS_API_KEY
        }
        response = requests.get(
            f"{STORMGLASS_BASE_URL}/{endpoint}",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_current_weather(latitude: Optional[float] = None, longitude: Optional[float] = None,
                       location_name: Optional[str] = None, country_code: str = "") -> Dict:
    """
    Get current weather conditions at a specific location.
    
    Args:
        latitude: Latitude of the location (optional if location_name provided)
        longitude: Longitude of the location (optional if location_name provided)
        location_name: Name of the location to geocode (optional if coordinates provided)
        country_code: Optional country code for geocoding (e.g., "KE" for Kenya)
    
    Returns:
        Dictionary with current weather data including temperature, humidity, wind, etc.
    """
    # Get coordinates from location name or use provided coordinates
    coords = get_coordinates(location_name, latitude, longitude, country_code)
    if not coords.get("success"):
        return coords
    
    lat = coords["latitude"]
    lng = coords["longitude"]
    
    params = {
        "lat": lat,
        "lng": lng,
        "params": "airTemperature,humidity,pressure,windSpeed,windDirection,visibility,cloudCover,precipitation"
    }
    
    result = _make_request("weather/point", params)
    
    if result and "error" not in result:
        # Extract current hour data
        if "hours" in result and len(result["hours"]) > 0:
            current_data = result["hours"][0]
            response = {
                "latitude": lat,
                "longitude": lng,
                "time": current_data.get("time", ""),
                "air_temperature": current_data.get("airTemperature", {}).get("sg", None),
                "humidity": current_data.get("humidity", {}).get("sg", None),
                "pressure": current_data.get("pressure", {}).get("sg", None),
                "wind_speed": current_data.get("windSpeed", {}).get("sg", None),
                "wind_direction": current_data.get("windDirection", {}).get("sg", None),
                "visibility": current_data.get("visibility", {}).get("sg", None),
                "cloud_cover": current_data.get("cloudCover", {}).get("sg", None),
                "precipitation": current_data.get("precipitation", {}).get("sg", None),
                "source": "Stormglass API"
            }
            # Add location info if geocoded
            if coords.get("source") == "geocoded":
                response["location_name"] = coords.get("location_name")
                response["country"] = coords.get("country")
                response["admin1"] = coords.get("admin1")
            return response
        else:
            return {"error": "No weather data available for this location"}
    
    return result or {"error": "Failed to fetch weather data"}


def get_weather_forecast(latitude: Optional[float] = None, longitude: Optional[float] = None,
                        location_name: Optional[str] = None, country_code: str = "", hours: int = 24) -> Dict:
    """
    Get weather forecast for a specific location.
    
    Args:
        latitude: Latitude of the location (optional if location_name provided)
        longitude: Longitude of the location (optional if location_name provided)
        location_name: Name of the location to geocode (optional if coordinates provided)
        country_code: Optional country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (default: 24, max: 240)
    
    Returns:
        Dictionary with forecast data for the specified time period
    """
    # Get coordinates from location name or use provided coordinates
    coords = get_coordinates(location_name, latitude, longitude, country_code)
    if not coords.get("success"):
        return coords
    
    lat = coords["latitude"]
    lng = coords["longitude"]
    
    if hours > 240:
        hours = 240
    if hours < 1:
        hours = 1
    
    # Calculate end time
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=hours)
    
    params = {
        "lat": lat,
        "lng": lng,
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "params": "airTemperature,humidity,pressure,windSpeed,windDirection,visibility,cloudCover,precipitation"
    }
    
    result = _make_request("weather/point", params)
    
    if result and "error" not in result:
        forecast_hours = result.get("hours", [])
        response = {
            "latitude": lat,
            "longitude": lng,
            "forecast_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": len(forecast_hours),
            "forecast": [
                {
                    "time": hour.get("time", ""),
                    "air_temperature": hour.get("airTemperature", {}).get("sg", None),
                    "humidity": hour.get("humidity", {}).get("sg", None),
                    "wind_speed": hour.get("windSpeed", {}).get("sg", None),
                    "wind_direction": hour.get("windDirection", {}).get("sg", None),
                    "precipitation": hour.get("precipitation", {}).get("sg", None),
                    "cloud_cover": hour.get("cloudCover", {}).get("sg", None),
                }
                for hour in forecast_hours
            ],
            "source": "Stormglass API"
        }
        # Add location info if geocoded
        if coords.get("source") == "geocoded":
            response["location_name"] = coords.get("location_name")
            response["country"] = coords.get("country")
            response["admin1"] = coords.get("admin1")
        return response
    
    return result or {"error": "Failed to fetch forecast data"}


def get_marine_weather(latitude: Optional[float] = None, longitude: Optional[float] = None,
                      location_name: Optional[str] = None, country_code: str = "", hours: int = 24) -> Dict:
    """
    Get marine weather data including wave height, swell, and sea conditions.
    
    Args:
        latitude: Latitude of the location (optional if location_name provided)
        longitude: Longitude of the location (optional if location_name provided)
        location_name: Name of the location to geocode (optional if coordinates provided)
        country_code: Optional country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (default: 24, max: 240)
    
    Returns:
        Dictionary with marine weather data including waves, swell, and sea conditions
    """
    # Get coordinates from location name or use provided coordinates
    coords = get_coordinates(location_name, latitude, longitude, country_code)
    if not coords.get("success"):
        return coords
    
    lat = coords["latitude"]
    lng = coords["longitude"]
    
    if hours > 240:
        hours = 240
    if hours < 1:
        hours = 1
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=hours)
    
    params = {
        "lat": lat,
        "lng": lng,
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "params": "waveHeight,waveDirection,wavePeriod,swellHeight,swellDirection,swellPeriod,seaLevel,waterTemperature"
    }
    
    result = _make_request("weather/point", params)
    
    if result and "error" not in result:
        marine_hours = result.get("hours", [])
        response = {
            "latitude": lat,
            "longitude": lng,
            "forecast_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": len(marine_hours),
            "marine_data": [
                {
                    "time": hour.get("time", ""),
                    "wave_height": hour.get("waveHeight", {}).get("sg", None),
                    "wave_direction": hour.get("waveDirection", {}).get("sg", None),
                    "wave_period": hour.get("wavePeriod", {}).get("sg", None),
                    "swell_height": hour.get("swellHeight", {}).get("sg", None),
                    "swell_direction": hour.get("swellDirection", {}).get("sg", None),
                    "swell_period": hour.get("swellPeriod", {}).get("sg", None),
                    "sea_level": hour.get("seaLevel", {}).get("sg", None),
                    "water_temperature": hour.get("waterTemperature", {}).get("sg", None),
                }
                for hour in marine_hours
            ],
            "source": "Stormglass API"
        }
        # Add location info if geocoded
        if coords.get("source") == "geocoded":
            response["location_name"] = coords.get("location_name")
            response["country"] = coords.get("country")
            response["admin1"] = coords.get("admin1")
        return response
    
    return result or {"error": "Failed to fetch marine weather data"}


def get_comprehensive_weather(latitude: Optional[float] = None, longitude: Optional[float] = None,
                             location_name: Optional[str] = None, country_code: str = "", hours: int = 24) -> Dict:
    """
    Get comprehensive weather data including both standard and marine weather.
    
    Args:
        latitude: Latitude of the location (optional if location_name provided)
        longitude: Longitude of the location (optional if location_name provided)
        location_name: Name of the location to geocode (optional if coordinates provided)
        country_code: Optional country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (default: 24, max: 240)
    
    Returns:
        Dictionary with comprehensive weather and marine data
    """
    # Get coordinates from location name or use provided coordinates
    coords = get_coordinates(location_name, latitude, longitude, country_code)
    if not coords.get("success"):
        return coords
    
    lat = coords["latitude"]
    lng = coords["longitude"]
    
    if hours > 240:
        hours = 240
    if hours < 1:
        hours = 1
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=hours)
    
    # Request all available parameters
    params = {
        "lat": lat,
        "lng": lng,
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "params": "airTemperature,humidity,pressure,windSpeed,windDirection,visibility,cloudCover,precipitation,waveHeight,waveDirection,wavePeriod,swellHeight,swellDirection,swellPeriod,seaLevel,waterTemperature"
    }
    
    result = _make_request("weather/point", params)
    
    if result and "error" not in result:
        all_hours = result.get("hours", [])
        response = {
            "latitude": lat,
            "longitude": lng,
            "forecast_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": len(all_hours),
            "comprehensive_data": [
                {
                    "time": hour.get("time", ""),
                    # Standard weather
                    "air_temperature": hour.get("airTemperature", {}).get("sg", None),
                    "humidity": hour.get("humidity", {}).get("sg", None),
                    "pressure": hour.get("pressure", {}).get("sg", None),
                    "wind_speed": hour.get("windSpeed", {}).get("sg", None),
                    "wind_direction": hour.get("windDirection", {}).get("sg", None),
                    "visibility": hour.get("visibility", {}).get("sg", None),
                    "cloud_cover": hour.get("cloudCover", {}).get("sg", None),
                    "precipitation": hour.get("precipitation", {}).get("sg", None),
                    # Marine weather
                    "wave_height": hour.get("waveHeight", {}).get("sg", None),
                    "wave_direction": hour.get("waveDirection", {}).get("sg", None),
                    "wave_period": hour.get("wavePeriod", {}).get("sg", None),
                    "swell_height": hour.get("swellHeight", {}).get("sg", None),
                    "swell_direction": hour.get("swellDirection", {}).get("sg", None),
                    "swell_period": hour.get("swellPeriod", {}).get("sg", None),
                    "sea_level": hour.get("seaLevel", {}).get("sg", None),
                    "water_temperature": hour.get("waterTemperature", {}).get("sg", None),
                }
                for hour in all_hours
            ],
            "source": "Stormglass API"
        }
        # Add location info if geocoded
        if coords.get("source") == "geocoded":
            response["location_name"] = coords.get("location_name")
            response["country"] = coords.get("country")
            response["admin1"] = coords.get("admin1")
        return response
    
    return result or {"error": "Failed to fetch comprehensive weather data"}


def geocode_location(location_name: str, country_code: str = "") -> Dict:
    """
    Geocode a location name to get latitude and longitude coordinates.
    Uses Open-Meteo's free geocoding API (no API key required).
    
    Args:
        location_name: Name of the location (city, address, etc.)
        country_code: Optional ISO-3166-1 alpha2 country code (e.g., "KE" for Kenya)
    
    Returns:
        Dictionary with location information and coordinates, or error if not found
    """
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": location_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        if country_code:
            params["country_code"] = country_code
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return {
                "success": True,
                "location_name": location_name,
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "name": result.get("name", location_name),
                "country": result.get("country", ""),
                "admin1": result.get("admin1", ""),  # State/Province
                "timezone": result.get("timezone", ""),
                "country_code": result.get("country_code", ""),
                "source": "Open-Meteo Geocoding API"
            }
        else:
            return {
                "success": False,
                "error": f"Location '{location_name}' not found",
                "location_name": location_name
            }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Geocoding API request failed: {str(e)}",
            "location_name": location_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during geocoding: {str(e)}",
            "location_name": location_name
        }


def get_coordinates(location_name: Optional[str] = None, latitude: Optional[float] = None, 
                   longitude: Optional[float] = None, country_code: str = "") -> Dict:
    """
    Get coordinates from either a location name (geocoding) or directly provided coordinates.
    This is a helper function that handles both cases.
    
    Args:
        location_name: Name of the location (will be geocoded if provided)
        latitude: Direct latitude value (if provided, takes precedence)
        longitude: Direct longitude value (if provided, takes precedence)
        country_code: Optional country code for geocoding
    
    Returns:
        Dictionary with coordinates and location info, or error
    """
    # If coordinates are provided directly, use them
    if latitude is not None and longitude is not None:
        valid, error_msg = _validate_coordinates(latitude, longitude)
        if not valid:
            return {
                "success": False,
                "error": error_msg,
                "latitude": latitude,
                "longitude": longitude
            }
        return {
            "success": True,
            "latitude": latitude,
            "longitude": longitude,
            "source": "direct_coordinates"
        }
    
    # If location name is provided, geocode it
    if location_name:
        geocode_result = geocode_location(location_name, country_code)
        if geocode_result.get("success"):
            return {
                "success": True,
                "latitude": geocode_result["latitude"],
                "longitude": geocode_result["longitude"],
                "location_name": geocode_result.get("name", location_name),
                "country": geocode_result.get("country", ""),
                "admin1": geocode_result.get("admin1", ""),
                "timezone": geocode_result.get("timezone", ""),
                "source": "geocoded"
            }
        else:
            return geocode_result
    
    # Neither provided
    return {
        "success": False,
        "error": "Either location_name or both latitude and longitude must be provided"
    }


def _validate_coordinates(latitude: float, longitude: float) -> tuple:
    """Validate latitude and longitude values."""
    if not (-90 <= latitude <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, None

