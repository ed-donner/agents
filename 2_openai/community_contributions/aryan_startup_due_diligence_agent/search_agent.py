import os
from openai import AsyncOpenAI
from agents import Agent, WebSearchTool, ModelSettings, OpenAIChatCompletionsModel

INSTRUCTIONS = (
    "You are a research agent in a startup due diligence pipeline. Given a search query, search the web and return a concise summary of findings.\n"
    "The summary must be 2-3 paragraphs and under 300 words. Capture only facts relevant to market size, growth trends, competitors, or industry dynamics. \n"
    "Write tersely — no complete sentences required, no filler. This output will be consumed by an analyst agent synthesizing a due diligence report, \n"
    "so precision matters more than polish.Do not analyze, interpret, or recommend. Only report what you find. Do not include any commentary, preamble,\n"
    "or closing remarks outside the summary itself."
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash-lite",
    openai_client=AsyncOpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ.get("GEMINI_API_KEY"),
    ),
)

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model=gemini_model,
    model_settings=ModelSettings(tool_choice="required"),
)