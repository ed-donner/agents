import os
from agents import Agent, OpenAIChatCompletionsModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from constants import gemini_default_model

load_dotenv(override=True)

# deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
gemini_client = AsyncOpenAI(base_url=os.environ.get("GEMINI_BASE_URL"), api_key=os.environ.get("GOOGLE_API_KEY"))
# groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=groq_api_key)

# deepseek_model = OpenAIChatCompletionsModel(model=deepseek_default_model, openai_client=deepseek_client)
gemini_model = OpenAIChatCompletionsModel(model=gemini_default_model, openai_client=gemini_client)
# llama3_3_model = OpenAIChatCompletionsModel(model=groq_default_model, openai_client=groq_client)

class EvaluationModel(BaseModel):
  is_satisfied: bool
  feedback: str

INSTRUCTIONS = (
  "You are an evaluator for Research Data. Your job is to evaluate the findings given to you as part of research against the query for research."
  "You analyze the query provided for research and research findings given to you, you provide feedback based on your anlysis"
  f"You always provide feedback in {EvaluationModel} format"
)

evaluator_agent = Agent(
  "evaluator_agent",
  instructions=INSTRUCTIONS,
  model=gemini_model,
  output_type=EvaluationModel
)


