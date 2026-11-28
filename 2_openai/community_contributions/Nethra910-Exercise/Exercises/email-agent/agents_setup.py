from agents import Agent,OpenAIChatCompletionsModel,ModelSettings
from openai import AsyncOpenAI

from context import instructions1,instructions2,instructions3,decision
from tools import send_email_tool
from config import GROQ_API_KEY



groq_client = AsyncOpenAI(
    base_url = "https://api.groq.com/openai/v1",
    api_key = GROQ_API_KEY
)

groq_model = OpenAIChatCompletionsModel(
    model = "openai/gpt-oss-120b",
    openai_client = groq_client
)

email_agent1 = Agent(
    name = "Professional Email Agent",
    instructions = instructions1,
    model = groq_model
)
email_agent2 = Agent(
    name = "Humorous Email Agent",
    instructions = instructions2,
    model = groq_model
)
email_agent3 = Agent(
    name = "Executive Email Agent",
    instructions = instructions3,
    model = groq_model
)

tool_requied = ModelSettings(tool_choice = "required")

email_picker = Agent(
    name = "Email Picker Agent",
    instructions = decision,
    model = groq_model,
    tools = [send_email_tool],
    model_settings = tool_requied
)