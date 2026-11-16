import os

from agents import Agent, OpenAIChatCompletionsModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from prompts import (
    instructions1,
    instructions2,
    instructions3,
    sales_instructions,
    critic_instructions,
)
from tools import send_message

load_dotenv()

BASE_URL = "https://openrouter.ai/api/v1"

API_KEY = os.getenv("OPENROUTER_API_KEY")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

model = OpenAIChatCompletionsModel(
    model="moonshotai/kimi-k2.6", openai_client=openrouter_client
)

prof_sales_agent = Agent(
    name="Professional Sales Agent", instructions=instructions1, model=model
)
humour_sales_agent = Agent(
    name="Humorous Sales Agent", instructions=instructions2, model=model
)
exec_sales_agent = Agent(
    name="Executive Sales Agent", instructions=instructions3, model=model
)

description = "Use this tool to write a sales email. In the input, just instruct it to write a sales email."

email_critic = Agent(name="Email critic", instructions=critic_instructions, model=model)


sales_manager = Agent(
    "Sales manager",
    instructions=sales_instructions,
    model=model,
    tools=[
        send_message,
        prof_sales_agent.as_tool(
            tool_name="prof_email_writer", tool_description=description
        ),
        humour_sales_agent.as_tool(
            tool_name="humour_email_writer", tool_description=description
        ),
        exec_sales_agent.as_tool(
            tool_name="exec_email_writer", tool_description=description
        ),
        email_critic.as_tool(
            tool_name="evaluate_email_drafts",
            tool_description="Compare drafts and select the most effective email.",
        ),
    ],
    handoffs=[],
)
