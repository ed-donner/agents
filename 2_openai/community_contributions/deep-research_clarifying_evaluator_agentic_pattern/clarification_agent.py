from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
from constants import gemini_default_model
import os
from models import Clarification

load_dotenv(override=True)

gemini_client = AsyncOpenAI(base_url=os.environ.get("GEMINI_BASE_URL"), api_key=os.environ.get("GOOGLE_API_KEY"))
# groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

# deepseek_model = OpenAIChatCompletionsModel(model=deepseek_default_model, openai_client=deepseek_client)
gemini_model = OpenAIChatCompletionsModel(model=gemini_default_model, openai_client=gemini_client)

CLARIFYING_QUESTIONS = 3

INSTRUCTIONS = (
  "You are a senior research assistant."
  "Given a query, your job is to come up with clarifying questions related to the query."
  f"Come up with atleast {CLARIFYING_QUESTIONS} clarifying questions."
)

clarification_agent = Agent("clarification_agent", instructions=INSTRUCTIONS, model=gemini_model, output_type=Clarification)