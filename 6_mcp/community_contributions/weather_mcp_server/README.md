# Weather MCP Server

A Model Context Protocol (MCP) server for fetching comprehensive weather data using the Stormglass API.

## Overview

This MCP server provides tools to access weather data from Stormglass, including:
- Current weather conditions
- Weather forecasts (up to 240 hours / 10 days)
- Marine weather data (waves, swell, sea conditions)
- Comprehensive weather data (combining standard + marine)

## Files

- `weather_researcher.py` - Helper functions for fetching weather data from Stormglass API
- `weather_server.py` - MCP server exposing weather tools
- `weather_demo.ipynb` - Demo notebook showing all features
- `push_server.py` - Push notification server for query completion alerts
- `README.md` - This documentation

## Prerequisites

1. **Stormglass API Key**: Sign up at [Stormglass.io](https://stormglass.io/) to get your API key
2. **Environment Variables**: Add `STORMGLASS_API_KEY` to your `.env` file
3. **Optional**: Add `PUSHOVER_USER` and `PUSHOVER_TOKEN` for push notifications

## Tools Provided

1. **get_current_weather_tool** - Get real-time weather conditions
   - Parameters: `location_name` (optional), `latitude` (optional), `longitude` (optional), `country_code` (optional)
   - You can provide EITHER `location_name` OR coordinates
   - Returns: Current temperature, humidity, pressure, wind speed/direction, visibility, cloud cover, precipitation

2. **get_weather_forecast_tool** - Get hourly weather forecast
   - Parameters: `location_name` (optional), `latitude` (optional), `longitude` (optional), `country_code` (optional), `hours` (1-240, default: 24)
   - You can provide EITHER `location_name` OR coordinates
   - Returns: Forecast data for specified time period

3. **get_marine_weather_tool** - Get marine weather data
   - Parameters: `location_name` (optional), `latitude` (optional), `longitude` (optional), `country_code` (optional), `hours` (1-240, default: 24)
   - You can provide EITHER `location_name` OR coordinates
   - Returns: Wave height, direction, period, swell conditions, sea level, water temperature

4. **get_comprehensive_weather_tool** - Get both standard and marine weather
   - Parameters: `location_name` (optional), `latitude` (optional), `longitude` (optional), `country_code` (optional), `hours` (1-240, default: 24)
   - You can provide EITHER `location_name` OR coordinates
   - Returns: Complete weather picture including land and sea conditions

5. **geocode_location_tool** - Convert location names to coordinates
   - Parameters: `location_name`, `country_code` (optional)
   - Returns: Latitude, longitude, country, and location details

## Resources Provided

- `weather://api-status` - Current status of the Stormglass API
- `weather://documentation` - Documentation about available tools and usage

## Usage

### Running from the weather_mcp Directory

**IMPORTANT**: The notebook (`weather_demo.ipynb`) is designed to run from the `weather_mcp` directory.

### Running the MCP Server

From the `weather_mcp` directory:

```python
from agents.mcp import MCPServerStdio

params = {"command": "uv", "args": ["run", "weather_server.py"]}

async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
    tools = await server.list_tools()
    print(tools)
```

### Using with an Agent

From the `weather_mcp` directory:

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Weather Server
weather_params = {"command": "uv", "args": ["run", "weather_server.py"]}

# Push Notification Server (optional)
push_params = {"command": "uv", "args": ["run", "push_server.py"]}

async with MCPServerStdio(params=weather_params, client_session_timeout_seconds=60) as weather_server:
    async with MCPServerStdio(params=push_params, client_session_timeout_seconds=60) as push_server:
        agent = Agent(
            name="weather_assistant",
            instructions="You are a weather assistant that helps users get weather information.",
            model="gpt-4o-mini",
            mcp_servers=[weather_server, push_server]
        )
        
        result = await Runner.run(
            agent,
            "Get current weather for Nairobi, Kenya"
        )
        print(result.final_output)
```

## Location Input Options

### Option 1: Use Location Names (Recommended)
You can simply provide a location name and the tool will automatically geocode it:
- `location_name="Nairobi, Kenya"`
- `location_name="New York, USA"`
- `location_name="Mombasa"` (with optional `country_code="KE"`)

### Option 2: Use Coordinates Directly
You can also provide coordinates directly if you have them:
- `latitude=1.2921, longitude=36.8219` (Nairobi, Kenya)
- `latitude=-4.0435, longitude=39.6682` (Mombasa, Kenya)
- `latitude=40.7128, longitude=-74.0060` (New York, USA)

**Note**: If both location name and coordinates are provided, coordinates take precedence.

### Coordinate Format (if providing directly)
- **Latitude**: -90 to 90 (negative for South, positive for North)
- **Longitude**: -180 to 180 (negative for West, positive for East)

## Implementation Notes

- The server uses the Stormglass API v2 endpoint for weather data
- **Automatic geocoding** is provided via Open-Meteo's free geocoding API (no API key required)
- You can use location names OR coordinates - geocoding happens automatically
- Forecasts can be requested for up to 240 hours (10 days)
- Marine weather data is particularly useful for coastal locations
- The server includes comprehensive error handling and logging
- Input validation ensures coordinates are within valid ranges
- Geocoding uses Open-Meteo API: https://geocoding-api.open-meteo.com/v1/search

## Dependencies

- `requests` - HTTP requests to Stormglass API
- `python-dotenv` - Environment variable management
- `mcp` - Model Context Protocol server framework

## API Documentation

For more information about the Stormglass API, visit:
- [Stormglass.io](https://stormglass.io/)
- [Stormglass API Documentation](https://docs.stormglass.io/)

## Error Handling

The server gracefully handles:
- Missing API key
- Invalid coordinates
- API request failures
- Network timeouts
- Invalid parameters

All errors are logged and returned in a structured format.

