from agents import Agent, function_tool, ModelSettings, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from messenger import send_email, push
import os
from dotenv import load_dotenv
load_dotenv(override=True)

MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

gemini_client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

gemini_model = OpenAIChatCompletionsModel(
    model=MODEL_NAME,
    openai_client=gemini_client
)

USE_EMAIL = os.getenv("USE_EMAIL", "true").lower() == "true"

settings = ModelSettings(tool_choice="required")

@function_tool
def send_email_tool(subject: str, text_body: str, html_body: str, recipient_email: str = "") -> str:
    """
    Send out an email with the given subject and body
    
    Args:
        subject: The subject of the email
        text_body: The body of the email as plain text
        html_body: The HTML body of the email
        recipient_email: Optional recipient email address to send the report to.
    """
    if USE_EMAIL:
        send_email(subject, text_body, html_body, to_email=recipient_email)
    else:
        push(f"Subject: {subject}\nTo: {recipient_email}\n\n{text_body}")
    return "Email sent successfully"


INSTRUCTIONS = """
You are provided with a detailed research report (and optionally a Recipient Email). Use your tool to send an email, converting the entire report into
a clean, well presented HTML email with an appropriate subject line.
If a Recipient Email is provided in the input, pass it to the recipient_email parameter of send_email_tool.
CRITICAL: You MUST include the full and complete report content in both the text_body and html_body.
Do NOT summarize, truncate, omit, or shorten any section of the report under any circumstances.
"""

email_agent = Agent(name="Email Agent", instructions=INSTRUCTIONS, tools=[send_email_tool], model=gemini_model, model_settings=settings)