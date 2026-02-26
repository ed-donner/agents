"""AIObot - AI Activity Assistant with MCP Weather and Event Search."""

import asyncio
import logging
import os
from datetime import datetime

import gradio as gr
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from events_service import EventsService
from weather_service import WeatherService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL = os.getenv("MODEL", "gpt-4o-mini")
MAX_ACTIVITIES = 10

SYSTEM_PROMPT = """
You are a fun, helpful assistant for an Activity Suggestion App.
Recommend **up to {nb_activity} activities** based on real-time weather, balancing indoor, outdoor, and event-based options.

---

### **Core Rules**
- **Total limit**: 10 activities maximum (nb_events + nb_indoors + nb_outdoors ≤ 10)
- **One response**: Provide all suggestions at once—no waiting
- **Smart balancing**: Adjust mix based on weather, event availability, and user needs
- **Default date**: If no date specified, assume today

---

### **Date Interpretation**
Reference date: **{today_str} ({day_name})**
- "Tomorrow" = today + 1 day
- "Next Monday" = closest upcoming Monday
- "This weekend" = upcoming Saturday & Sunday
- Date ranges = calculate from today (e.g., "next 3 days" = today + 2)
- **Don't ask for confirmation**—interpret confidently

---

### **Process (All in One Go)**
1. **Get weather** for user's location and requested date
2. **Suggest activities** matching weather conditions
3. **Fetch events** from Ticketmaster (if available)
4. **Combine everything** into one structured response

---

### **Weather API**
- Calculate days offset for relative dates
- Show forecast only for requested date
- Limit: 14-day forecast (inform user if beyond range)
- If unavailable: notify in a friendly way

---

### **Ticketmaster API**
- Use ISO Alpha-2 country codes (FR, US, CA, DK, etc.)
- **Date mapping**:
  - "Today" → today's date
  - "Next Monday" → next occurrence of that day
  - "Next 3 days" → today as start date
- If >5 events found: ask for one-word interest (music, cinema, theater)
- If no events: inform user in a fun way
- **Never mention "Ticketmaster"**—just say "checking for events"

---

### **User Interaction**
- **No city provided?** → Ask for it
- **Event search fails?** → Say "no events found" (don't mention Ticketmaster)
- **Provide everything in one response**

---

### **Event Formatting**
When events are available:

Here are some events that may interest you:

**Event Name**:
- 📅 Date: 19th March 2025
- 📍 Venue: [venue name]
- 🔗 [Ticket Link](URL)

---

### **Tone**
Be **short, fun, and accurate** with a dash of humor! Keep users smiling while delivering the best suggestions! 🎉
"""


class ActivityAssistant:
    """Main assistant class that coordinates weather, events, and agent."""

    def __init__(self):
        """Initialize services and agent."""
        logger.info("Initializing ActivityAssistant...")
        self.weather_service = WeatherService()
        self.events_service = EventsService()
        self.agent = self._create_agent()
        logger.info("ActivityAssistant initialized successfully")

    def _create_system_message(self):
        """Create system prompt with current date."""
        today_str = datetime.today().strftime("%Y-%m-%d")
        day_name = datetime.today().strftime("%A")
        return SYSTEM_PROMPT.format(
            nb_activity=MAX_ACTIVITIES, today_str=today_str, day_name=day_name
        )

    def _create_weather_tool(self):
        """Create weather tool using MCP server."""
        weather_service = self.weather_service

        @function_tool
        async def get_weather(city: str, days: int = 7) -> dict:
            """Get the current weather and forecast for a city.

            Args:
                city: The city for which the weather is being requested
                days: The number of days for the weather forecast (1-14 days)

            Returns:
                Dictionary containing weather forecast data
            """
            logger.info(f"Fetching weather for {city} ({days} days)")
            try:
                weather_data = await weather_service.get_weather(city, days)
                if "error" in weather_data:
                    logger.error(f"Weather API error: {weather_data['error']}")
                    return {"error": weather_data["error"]}
                logger.info(f"Weather data retrieved for {city}")
                return {"weather": weather_data}
            except Exception as e:
                logger.error(f"Weather tool exception: {str(e)}")
                return {"error": str(e)}

        return get_weather

    def _create_events_tool(self):
        """Create Ticketmaster events search tool."""
        events_service = self.events_service

        @function_tool
        async def get_ticketmaster_events(
            city: str,
            country_code: str,
            start_date: str,
            keywords: list[str] | None = None,
        ) -> dict:
            """Fetch upcoming events from Ticketmaster.

            Args:
                city: City where the events are searched
                country_code: ISO Alpha-2 country code (US, GB, CA, etc.)
                start_date: Start date for the event search (YYYY-MM-DD format)
                keywords: Optional keywords for event search (e.g., 'music', 'concert')

            Returns:
                Dictionary containing event data
            """
            logger.info(f"Searching events in {city}, {country_code} (date: {start_date}, keywords: {keywords})")
            try:
                # Convert date to ISO format with timezone
                if start_date:
                    start_date = str(start_date) + "T00:00:00Z"

                events = await events_service.search_events(
                    city, country_code, keywords, start_date
                )

                if isinstance(events, dict) and "error" in events:
                    logger.error(f"Events API error: {events['error']}")
                    return events

                if events:
                    logger.info(f"Found {len(events)} events in {city}")
                    return {"events": events}
                else:
                    logger.info(f"No events found in {city}")
                    return {"message": "No events found for this location."}
            except Exception as e:
                logger.error(f"Events tool exception: {str(e)}")
                return {"error": str(e)}

        return get_ticketmaster_events

    def _create_agent(self):
        """Create the OpenAI Agent with tools."""
        instructions = self._create_system_message()
        tools = [self._create_weather_tool(), self._create_events_tool()]

        agent = Agent(
            name="Activity Assistant",
            instructions=instructions,
            model=MODEL,
            tools=tools,
        )
        return agent

    async def chat_async(self, message: str) -> str:
        """Process chat message and return response.

        Args:
            message: User message

        Returns:
            Response string
        """
        logger.info(f"Received message: {message[:100]}...")

        # Run agent with just the message
        result = await Runner.run(
            self.agent,
            message
        )

        response = result.final_output or "Sorry, I couldn't generate a response."
        logger.info(f"Generated response ({len(response)} chars)")
        return response

    def chat(self, message: str) -> str:
        """Sync wrapper for Gradio ChatInterface.

        Args:
            message: User message

        Returns:
            Response string
        """
        return asyncio.run(self.chat_async(message))


def create_ui(assistant: ActivityAssistant):
    """Create Gradio chat interface."""

    def respond(message, history):
        """Wrapper function for ChatInterface."""
        # For now, just pass the message (stateless)
        # Each request is independent
        return assistant.chat(message)

    demo = gr.ChatInterface(
        fn=respond,
        title="🤖 AIObot - Your AI Activity Assistant",
        description="Ask me for activity suggestions based on weather and local events!",
        examples=[
            "What can I do in Paris this weekend?",
            "Suggest activities for tomorrow in London",
            "What's happening in New York next week?"
        ],
        chatbot=gr.Chatbot(height=500),
    )

    return demo


def main():
    """Run the application."""
    logger.info("Starting AIObot application...")

    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")
    if not os.getenv("TICKETMASTER_KEY"):
        raise ValueError("TICKETMASTER_KEY environment variable is required")
    if not os.getenv("WEATHERAPI_KEY"):
        raise ValueError("WEATHERAPI_KEY environment variable is required")

    logger.info("All API keys verified")

    # Create assistant and UI
    assistant = ActivityAssistant()
    demo = create_ui(assistant)

    # Launch
    logger.info("Launching Gradio interface on http://0.0.0.0:7860")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
