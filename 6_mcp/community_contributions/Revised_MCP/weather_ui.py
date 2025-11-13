import os
import asyncio
import gradio as gr
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from agents import (
    Runner, 
    Agent,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_export_api_key,
    trace,
    
)


client = AsyncOpenAI(
    #Anthropic API key
    api_key="my_anthropic_api_key",
    base_url="https://api.anthropic.com/v1",
)

set_default_openai_api('chat_completions')
set_default_openai_client(client)
set_tracing_export_api_key(os.getenv('OPENAI_API_KEY', '#openai api'))


MODEL = "claude-haiku-4-5"

# params
weather_params = {"command": "python", "args": ["server.py"]}


async def run_weather_agent(user_query: str):
    async with MCPServerStdio(params=weather_params, client_session_timeout_seconds=60) as weather_server:
        with trace("weather_assistant"):
            agent = Agent(
                name="weather_assistant",
                instructions=(
                    "You are a friendly and intelligent weather assistant. "
                    "You have access to real-time weather tools: "
                    "city_temp (°C), city_condition, city_humidity (%), city_wind (kph), "
                    "and weather_advice(temp, condition, humidity, wind).\n\n"
                    "When a user asks about the weather in a city:\n"
                    "1. Use city_temp, city_condition, city_humidity, and city_wind to gather data.\n"
                    "2. Pass those values to weather_advice() to get practical tips for the user.\n"
                    "3. Summarize everything clearly and conversationally — for example:\n"
                    "   'In Nairobi, it’s 23°C with light rain and 70% humidity. "
                    "Carry an umbrella and wear something light.'\n\n"
                    "Be natural, don’t just list numbers; help the user understand the weather experience."
                ),
                model=MODEL,
                mcp_servers=[weather_server],
            )

            result = await Runner.run(agent, user_query)
            return result.final_output


def query_weather(user_query: str):
    try:
        return asyncio.run(run_weather_agent(user_query))
    except Exception as e:
        return f"Error: {e}"


#UI
ui = gr.Interface(
    fn=query_weather,
    inputs=gr.Textbox(
        label="Request the weather in any city/town",
        placeholder="e.g. What's the weather like in London?",
    ),
    outputs=gr.Textbox(label="Weather information"),
    title="Weather Agent",
    description=(
        "Ask about any city's weather. This Claude-powered assistant uses MCP tools "
        "to fetch real data and give you personalized weather advice."
    ),
)

if __name__ == "__main__":
    ui.launch()
