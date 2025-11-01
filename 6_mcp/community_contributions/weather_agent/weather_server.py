from mcp.server.fastmcp import FastMCP
from weather import Weather

mcp = FastMCP("accounts_server")

@mcp.tool()
async def get_city_temperature(city: str) -> float:
    """Get the temperature of the given City in Celsius.

    Args:
        city: the name of the city
    """
    response = Weather.get_temperature_by_city(city)
    if response["success"]:
        return response["temperature_celsius"]
    else:
        raise Exception(response["error"])

@mcp.tool()
async def get_city_weather(city: str) -> str:
    """Get the weather of the given City.

    Args:
        city: the name of the city
    """
    response = Weather.get_weather_by_city(city)
    if response["success"]:
        return response["weather"]
    else:
        raise Exception(response["error"])

@mcp.tool()
async def get_city_humidity(city: str) -> int:
    """Get the humidity of the given City.

    Args:
        city: the name of the city
    """
    response = Weather.get_humidity_by_city(city)
    if response["success"]:
        return response["humidity"]
    else:
        raise Exception(response["error"])


@mcp.tool()
async def get_city_wind(city: str) -> float:
    """Get the wind of the given City in kph.

    Args:
        city: the name of the city
    """
    response = Weather.get_wind_by_city(city)
    if response["success"]:
        return response["wind_kph"]
    else:
        raise Exception(response["error"])

if __name__ == "__main__":
    mcp.run(transport='stdio')