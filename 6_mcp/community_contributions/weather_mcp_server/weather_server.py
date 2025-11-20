"""
Weather MCP Server
Comprehensive MCP server for weather data using Stormglass API.
Provides current weather, forecasts, and marine weather data.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP

# Add the current directory to Python path to ensure imports work
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import weather functions
try:
    from weather_researcher import (
        get_current_weather,
        get_weather_forecast,
        get_marine_weather,
        get_comprehensive_weather,
        geocode_location,
        STORMGLASS_AVAILABLE
    )
    logger.info("Weather module loaded successfully")
except ImportError as e:
    logger.warning(f"Weather module not available: {e}")
    STORMGLASS_AVAILABLE = False

mcp = FastMCP("weather_server")


def _handle_error(error: Exception, tool_name: str, context: str = "") -> Dict[str, Any]:
    """Centralized error handling for all tools."""
    error_msg = f"Error in {tool_name}"
    if context:
        error_msg += f" ({context})"
    error_msg += f": {str(error)}"
    
    logger.error(error_msg, exc_info=True)
    
    return {
        "error": True,
        "message": error_msg,
        "tool": tool_name,
        "context": context
    }


def _validate_coordinates(latitude: float, longitude: float) -> tuple:
    """Validate latitude and longitude values."""
    if not (-90 <= latitude <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, None


@mcp.tool()
async def get_current_weather_tool(
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country_code: str = ""
) -> str:
    """Get current weather conditions at a specific location.
    
    This tool fetches real-time weather data including temperature, humidity,
    pressure, wind speed and direction, visibility, cloud cover, and precipitation.
    
    You can provide either a location name (which will be geocoded) OR coordinates.
    If both are provided, coordinates take precedence.
    
    Args:
        location_name: Name of the location (e.g., "Nairobi, Kenya") - will be geocoded
        latitude: Latitude of the location (-90 to 90) - optional if location_name provided
        longitude: Longitude of the location (-180 to 180) - optional if location_name provided
        country_code: Optional ISO-3166-1 alpha2 country code for geocoding (e.g., "KE" for Kenya)
    
    Returns:
        JSON string containing current weather data
    """
    if not STORMGLASS_AVAILABLE:
        return json.dumps({
            "error": True,
            "message": "STORMGLASS_API_KEY not found in environment variables"
        }, indent=2)
    
    try:
        logger.info(f"Fetching current weather: location_name={location_name}, lat={latitude}, lng={longitude}")
        
        result = get_current_weather(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            country_code=country_code
        )
        
        if result.get("error") or not result.get("success", True):
            logger.warning(f"Failed to get current weather: {result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        error_result = _handle_error(e, "get_current_weather_tool", f"location={location_name or f'{latitude},{longitude}'}")
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def get_weather_forecast_tool(
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country_code: str = "",
    hours: int = 24
) -> str:
    """Get weather forecast for a specific location.
    
    This tool provides hourly weather forecasts including temperature, humidity,
    pressure, wind conditions, visibility, cloud cover, and precipitation.
    
    You can provide either a location name (which will be geocoded) OR coordinates.
    If both are provided, coordinates take precedence.
    
    Args:
        location_name: Name of the location (e.g., "Mombasa, Kenya") - will be geocoded
        latitude: Latitude of the location (-90 to 90) - optional if location_name provided
        longitude: Longitude of the location (-180 to 180) - optional if location_name provided
        country_code: Optional ISO-3166-1 alpha2 country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (1-240, default: 24)
    
    Returns:
        JSON string containing forecast data
    """
    if not STORMGLASS_AVAILABLE:
        return json.dumps({
            "error": True,
            "message": "STORMGLASS_API_KEY not found in environment variables"
        }, indent=2)
    
    try:
        # Validate hours
        if hours < 1:
            hours = 1
        if hours > 240:
            hours = 240
        
        logger.info(f"Fetching weather forecast: location_name={location_name}, lat={latitude}, lng={longitude}, hours={hours}")
        
        result = get_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            country_code=country_code,
            hours=hours
        )
        
        if result.get("error") or not result.get("success", True):
            logger.warning(f"Failed to get forecast: {result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        error_result = _handle_error(e, "get_weather_forecast_tool", f"location={location_name or f'{latitude},{longitude}'}, hours={hours}")
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def get_marine_weather_tool(
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country_code: str = "",
    hours: int = 24
) -> str:
    """Get marine weather data including wave height, swell, and sea conditions.
    
    This tool is particularly useful for coastal and marine applications, providing
    detailed information about wave height, wave direction, wave period, swell conditions,
    sea level, and water temperature.
    
    You can provide either a location name (which will be geocoded) OR coordinates.
    If both are provided, coordinates take precedence.
    
    Args:
        location_name: Name of the location (e.g., "Mombasa, Kenya") - will be geocoded
        latitude: Latitude of the location (-90 to 90) - optional if location_name provided
        longitude: Longitude of the location (-180 to 180) - optional if location_name provided
        country_code: Optional ISO-3166-1 alpha2 country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (1-240, default: 24)
    
    Returns:
        JSON string containing marine weather data
    """
    if not STORMGLASS_AVAILABLE:
        return json.dumps({
            "error": True,
            "message": "STORMGLASS_API_KEY not found in environment variables"
        }, indent=2)
    
    try:
        # Validate hours
        if hours < 1:
            hours = 1
        if hours > 240:
            hours = 240
        
        logger.info(f"Fetching marine weather: location_name={location_name}, lat={latitude}, lng={longitude}, hours={hours}")
        
        result = get_marine_weather(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            country_code=country_code,
            hours=hours
        )
        
        if result.get("error") or not result.get("success", True):
            logger.warning(f"Failed to get marine weather: {result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        error_result = _handle_error(e, "get_marine_weather_tool", f"location={location_name or f'{latitude},{longitude}'}, hours={hours}")
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def get_comprehensive_weather_tool(
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    country_code: str = "",
    hours: int = 24
) -> str:
    """Get comprehensive weather data including both standard and marine weather.
    
    This tool combines standard weather data (temperature, wind, precipitation) with
    marine weather data (waves, swell, sea conditions) for a complete weather picture.
    Ideal for coastal locations or when you need both land and sea weather information.
    
    You can provide either a location name (which will be geocoded) OR coordinates.
    If both are provided, coordinates take precedence.
    
    Args:
        location_name: Name of the location (e.g., "Mombasa, Kenya") - will be geocoded
        latitude: Latitude of the location (-90 to 90) - optional if location_name provided
        longitude: Longitude of the location (-180 to 180) - optional if location_name provided
        country_code: Optional ISO-3166-1 alpha2 country code for geocoding (e.g., "KE" for Kenya)
        hours: Number of hours to forecast (1-240, default: 24)
    
    Returns:
        JSON string containing comprehensive weather and marine data
    """
    if not STORMGLASS_AVAILABLE:
        return json.dumps({
            "error": True,
            "message": "STORMGLASS_API_KEY not found in environment variables"
        }, indent=2)
    
    try:
        # Validate hours
        if hours < 1:
            hours = 1
        if hours > 240:
            hours = 240
        
        logger.info(f"Fetching comprehensive weather: location_name={location_name}, lat={latitude}, lng={longitude}, hours={hours}")
        
        result = get_comprehensive_weather(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            country_code=country_code,
            hours=hours
        )
        
        if result.get("error") or not result.get("success", True):
            logger.warning(f"Failed to get comprehensive weather: {result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        error_result = _handle_error(e, "get_comprehensive_weather_tool", f"location={location_name or f'{latitude},{longitude}'}, hours={hours}")
        return json.dumps(error_result, indent=2)


@mcp.tool()
async def geocode_location_tool(
    location_name: str,
    country_code: str = ""
) -> str:
    """Geocode a location name to get its latitude and longitude coordinates.
    
    This tool converts location names (cities, addresses, etc.) to geographic coordinates
    using Open-Meteo's free geocoding API. Useful for getting coordinates before calling
    weather tools, or for verifying location coordinates.
    
    Args:
        location_name: Name of the location to geocode (e.g., "Nairobi, Kenya", "New York, USA")
        country_code: Optional ISO-3166-1 alpha2 country code to narrow search (e.g., "KE" for Kenya)
    
    Returns:
        JSON string containing location information including latitude, longitude, country, etc.
    """
    try:
        logger.info(f"Geocoding location: {location_name}, country_code={country_code}")
        
        result = geocode_location(location_name, country_code)
        
        if result.get("success"):
            logger.info(f"Successfully geocoded: {result.get('name')} at {result.get('latitude')}, {result.get('longitude')}")
        else:
            logger.warning(f"Failed to geocode location: {result.get('error')}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        error_result = _handle_error(e, "geocode_location_tool", f"location={location_name}")
        return json.dumps(error_result, indent=2)


# Resources
@mcp.resource("weather://api-status")
async def read_api_status_resource() -> str:
    """Resource providing the current status of the weather API.
    
    Shows whether the Stormglass API is available and configured.
    """
    status = {
        "api_name": "Stormglass API",
        "api_available": STORMGLASS_AVAILABLE,
        "base_url": "https://api.stormglass.io/v2",
        "capabilities": [
            "Current weather conditions",
            "Weather forecasts (up to 240 hours)",
            "Marine weather data",
            "Comprehensive weather data",
            "Automatic geocoding (location names to coordinates)"
        ]
    }
    
    if not STORMGLASS_AVAILABLE:
        status["message"] = "STORMGLASS_API_KEY not found in environment variables. Please set it in your .env file."
    else:
        status["message"] = "API is configured and ready to use."
    
    return json.dumps(status, indent=2)


@mcp.resource("weather://documentation")
async def read_documentation_resource() -> str:
    """Resource providing documentation about the weather MCP server.
    
    Explains available tools, parameters, and usage examples.
    """
    return """Weather MCP Server Documentation

AVAILABLE TOOLS:

1. get_current_weather_tool
   - Get real-time weather conditions
   - Parameters: location_name (optional), latitude (optional), longitude (optional), country_code (optional)
   - You can provide EITHER location_name OR coordinates
   - Returns: Current temperature, humidity, pressure, wind, visibility, cloud cover, precipitation

2. get_weather_forecast_tool
   - Get hourly weather forecast
   - Parameters: location_name (optional), latitude (optional), longitude (optional), country_code (optional), hours (1-240, default: 24)
   - You can provide EITHER location_name OR coordinates
   - Returns: Forecast data for specified time period

3. get_marine_weather_tool
   - Get marine weather data (waves, swell, sea conditions)
   - Parameters: location_name (optional), latitude (optional), longitude (optional), country_code (optional), hours (1-240, default: 24)
   - You can provide EITHER location_name OR coordinates
   - Returns: Wave height, direction, period, swell conditions, sea level, water temperature

4. get_comprehensive_weather_tool
   - Get both standard and marine weather data
   - Parameters: location_name (optional), latitude (optional), longitude (optional), country_code (optional), hours (1-240, default: 24)
   - You can provide EITHER location_name OR coordinates
   - Returns: Complete weather picture including land and sea conditions

5. geocode_location_tool
   - Convert location names to coordinates
   - Parameters: location_name, country_code (optional)
   - Returns: Latitude, longitude, country, and location details

LOCATION INPUT:
- Option 1: Provide location_name (e.g., "Nairobi, Kenya") - will be automatically geocoded
- Option 2: Provide latitude and longitude directly
- If both are provided, coordinates take precedence

COORDINATE FORMAT (if providing directly):
- Latitude: -90 to 90 (negative for South, positive for North)
- Longitude: -180 to 180 (negative for West, positive for East)

EXAMPLES:
- Using location name: location_name="Nairobi, Kenya"
- Using coordinates: latitude=1.2921, longitude=36.8219
- With country code: location_name="Nairobi", country_code="KE"

For more information, visit: https://stormglass.io/
"""


if __name__ == "__main__":
    logger.info("Starting Weather MCP Server")
    logger.info(f"Stormglass API available: {STORMGLASS_AVAILABLE}")
    mcp.run(transport='stdio')

