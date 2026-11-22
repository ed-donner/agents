from pydantic import BaseModel, Field
from agents import Agent
import os
from dotenv import load_dotenv
load_dotenv(override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
HOW_MANY_SEARCHES = int(os.getenv("HOW_MANY_SEARCHES", 5))


INSTRUCTIONS = f"""
You are a research assistant. Given a user query, come up with a set of web searches
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.
"""

CLARIFYING_INSTRUCTIONS = f"""
You are a research clarification assistant. Given a user's initial research query, generate exactly 5 high-impact clarifying questions to uncover their true intent, scope, and constraints before starting the research.

Focus on identifying:
1. Target audience and depth (technical vs. executive summary).
2. Specific timeframe, geography, or domain boundaries.
3. Key angle, goal, or decision this research will support.
4. Desired output format or structure.
5. Any known exclusions or baseline assumptions.

Rules:
- Keep each question concise, direct, and easy to answer.
- Avoid redundant questions or asking for information already implied in the prompt.
- Output only the numbered list of 5 questions.
"""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class Question(BaseModel):
    question: str = Field(description="A clarifying questions for the user that its unswer will help me better understand the query.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

class ClarifyingQuestionsList(BaseModel):
    questions: list[Question] = Field(description="A list of clarifying questions to ask to better understand the query")
    
planner_agent = Agent(name="Planner Agent", instructions=INSTRUCTIONS, model=MODEL_NAME, output_type=WebSearchPlan)
clarifying_agent = Agent(name="Clarifying Agent", instructions=CLARIFYING_INSTRUCTIONS, model=MODEL_NAME, output_type=ClarifyingQuestionsList)