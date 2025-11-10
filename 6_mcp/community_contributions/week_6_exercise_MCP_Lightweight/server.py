from mcp.server.fastmcp import FastMCP
from sorrounding import Atmosphere

mcp_server = FastMCP("accounts_server")

@mcp_server.tool()
async def city_temp(city: str) -> float:
    response = Atmosphere.fetch_temperature(city)
    if response["success"]:
        return response["temperature_celsius"]
    else:
        raise Exception(response["error"])

@mcp_server.tool()
async def city_condition(city: str) -> str:
    response = Atmosphere.fetch_condition(city)
    if response["success"]:
        return response["weather"]
    else:
        raise Exception(response["error"])

@mcp_server.tool()
async def city_humidity(city: str) -> int:
    response = Atmosphere.fetch_humidity(city)
    if response["success"]:
        return response["humidity"]
    else:
        raise Exception(response["error"])

@mcp_server.tool()
async def city_wind(city: str) -> float:
    response = Atmosphere.fetch_wind_speed(city)
    if response["success"]:
        return response["wind_kph"]
    else:
        raise Exception(response["error"])

if __name__ == "__main__":
    mcp_server.run(transport='stdio')
