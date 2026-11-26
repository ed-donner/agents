from agents import Agent, OpenAIChatCompletionsModel, function_tool, ModelSettings
from openai import AsyncOpenAI
from messenger import send_email, push, send_telegram
import os
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "openai/gpt-4o-mini")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=OPENROUTER_API_KEY)
model = OpenAIChatCompletionsModel(openai_client=openrouter_client, model=MODEL_NAME)
USE_EMAIL = False


settings = ModelSettings(tool_choice="required")


@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
    """
    Send out an email with the given subject and body

    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
    """
    if USE_EMAIL:
        send_email(subject, text_body, html_body)
    else:
        message = f"""
    {subject}
    {text_body}
"""
        send_telegram(message)
    return "Email sent successfully"


INSTRUCTIONS = """
You are provided with a detailed report. Use your tool to send an email, converting the report into
a clean, well presented HTML email with an appropriate subject line.
"""

email_agent = Agent(
    name="Email Agent",
    instructions=INSTRUCTIONS,
    tools=[send_email_tool],
    model=model,
    model_settings=settings,
)
