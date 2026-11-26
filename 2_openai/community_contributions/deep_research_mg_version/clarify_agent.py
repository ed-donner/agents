from pydantic import BaseModel, Field
from agents import Agent
import os
from dotenv import load_dotenv
load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

CLARIFYING_INSTRUCTIONS = f"""
You are a research clarification assistant. Given a user's initial research query, generate exactly 3 high-impact clarifying questions to uncover their true intent, scope, and constraints before starting the research.

Focus on identifying:
1. Target audience and depth (technical vs. executive summary).
2. Specific timeframe, geography, or domain boundaries.
3. Key angle, goal, or decision this research will support.
4. Desired output format or structure.
5. Any known exclusions or baseline assumptions.

Rules:
- Keep each question concise, direct, and easy to answer.
- Avoid redundant questions or asking for information already implied in the prompt.
- Output only the numbered list of 3 questions.
"""

class Question(BaseModel):
    question: str = Field(description="A clarifying questions for the user that its unswer will help me better understand the query.")

class ClarifyingQuestionsList(BaseModel):
    questions: list[Question] = Field(description="A list of clarifying questions to ask to better understand the query")
    
clarifying_agent = Agent(name="Clarifying Agent", instructions=CLARIFYING_INSTRUCTIONS, model=MODEL_NAME, output_type=ClarifyingQuestionsList)