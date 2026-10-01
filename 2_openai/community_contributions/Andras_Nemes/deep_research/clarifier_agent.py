from pydantic import BaseModel, Field
from agents import Agent
from dotenv import load_dotenv
import os

load_dotenv(override=True)
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

HOW_MANY_QUESTIONS = 3

INSTRUCTIONS = f"""
You are a research assistant helping to scope a research request before any searching begins.
Given the user's query, ask exactly {HOW_MANY_QUESTIONS} concise clarifying questions that would
most help you target the research - for example the scope, the intended audience, the time frame,
the desired depth, or which aspects matter most. Only ask questions whose answers would genuinely
change how you research. Do not answer the query yourself; output only the questions.
"""


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description=f"Exactly {HOW_MANY_QUESTIONS} clarifying questions to ask the user."
    )


clarifier_agent = Agent(name="Clarifier Agent", instructions=INSTRUCTIONS, model=MODEL_NAME, output_type=ClarifyingQuestions)
