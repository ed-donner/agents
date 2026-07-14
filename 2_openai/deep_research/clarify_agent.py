from pydantic import Field, BaseModel
from agents import Agent, function_tool, ModelSettings
import os
from dotenv import load_dotenv
load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
HOW_MANY_QUESTIONS = 3

INSTRUCTIONS = f"""
You are a helpful assistant that clarifies the user's query. Output {HOW_MANY_QUESTIONS} questions based on the query.
"""

class ClarifyQuestion(BaseModel):
    question: str = Field(description="The question to ask the user.")
    answer: str | None = Field(description="The answer to the question.")


clarify_agent = Agent(
    name="Clarify Agent",
    model=MODEL_NAME,
    instructions=INSTRUCTIONS,
    output_type=list[ClarifyQuestion],
)