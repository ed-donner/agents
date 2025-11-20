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

@mcp_server.tool()
async def weather_advice(temp: float, condition: str, humidity: int, wind: float) -> str:
    tips = []

    if "rain" in condition.lower() or "drizzle" in condition.lower():
        tips.append("Carry an umbrella or raincoat. Besure to keep warm")
    if temp < 18:
        tips.append("Wear a warm jacket or sweater. It's chilly outside.")
    elif temp > 30:
        tips.append("Wear light clothing and stay hydrated. It's hot outside.")
    if wind > 25:
        tips.append("It's windy, secure your hat or avoid loose items. It's windy outside.")
    if humidity > 80:
        tips.append("It may feel sticky or muggy outside. It's humid outside.")

    if not tips:
        tips.append("The weather looks pleasant, enjoy your day!")

    return " ".join(tips)


if __name__ == "__main__":
    mcp_server.run(transport='stdio')
