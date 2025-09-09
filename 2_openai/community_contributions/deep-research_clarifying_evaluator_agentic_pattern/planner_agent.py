from agents import Agent
from pydantic import BaseModel, Field
from constants import default_model

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = (
  "You are a helpful research assistant. Given a query and associated clarifying questions, come up with a set of web searches to best answer the query. Tune the searches taking into"  
  " account the clarifications. Output {HOW_MANY_SEARCHES} terms to query for"
)

class ClarifyingQuestions(BaseModel):
  question: str = Field(description="")
  reason: str = Field(description="")

class WebSearchTerm(BaseModel):
  reason: str = Field(description="")
  search_term: str = Field(description="")
  clarifying_questions: list[ClarifyingQuestions] = Field(description="A list of clarifying questions ")

class WebSearchPlan(BaseModel):
  searches: list[WebSearchTerm] = Field(description="A list of web searches to perform to best answer the query")

planner_agent = Agent(
  "planner_agent",
  instructions=INSTRUCTIONS,
  model=default_model,
  output_type=WebSearchPlan
)


