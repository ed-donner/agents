"""Weather service using MCP (Model Context Protocol)."""

import logging
import os
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class WeatherService:
    """Weather service that uses MCP server for weather data.

    This demonstrates the Model Context Protocol (MCP) integration
    for accessing weather APIs through a standardized interface.
    Uses @swonixs/weatherapi-mcp npm package.
    """

    def __init__(self):
        """Initialize the WeatherService with MCP server configuration."""
        self.weather_api_key = os.getenv("WEATHERAPI_KEY")

        if not self.weather_api_key:
            raise ValueError(
                "WEATHERAPI_KEY environment variable is required for MCP weather service"
            )

    @asynccontextmanager
    async def _get_mcp_session(self):
        """Get MCP session context manager.

        This creates a connection to the MCP weather server running
        as a separate process via npx, demonstrating inter-process
        communication via the Model Context Protocol.
        """
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@swonixs/weatherapi-mcp"],
            env={"WEATHER_API_KEY": self.weather_api_key},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def get_weather(self, city: str, days: int = 7) -> dict:
        """Get current weather using MCP server."""
        try:
            logger.debug(f"Connecting to MCP weather server for {city}")
            async with self._get_mcp_session() as session:
                result = await session.call_tool(
                    "get_weather",
                    arguments={"location": city},
                )
                logger.debug(f"MCP weather response received for {city}")

                # Extract text content from MCP response
                weather_text = ""
                if isinstance(result.content, list):
                    for item in result.content:
                        if hasattr(item, 'text'):
                            weather_text += item.text
                elif hasattr(result.content, 'text'):
                    weather_text = result.content.text
                else:
                    weather_text = str(result.content)

                return {"weather": weather_text}
        except Exception as e:
            logger.error(f"MCP weather request failed: {e}")
            return {"error": f"Could not fetch weather for {city}: {str(e)}"}
