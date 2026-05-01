from agents import Agent, WebSearchTool, ModelSettings
from pydantic import BaseModel


# --- Planner ---

class SearchItem(BaseModel):
    query: str
    reason: str

class SearchPlan(BaseModel):
    searches: list[SearchItem]

planner = Agent(
    name="Planner",
    instructions="""
    Generate 5 useful search queries for the given research topic.
    """,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)


# --- Search ---

search_agent = Agent(
    name="Search",
    instructions="""
    Search and summarize results in 2-3 short paragraphs.
    """,
    tools=[WebSearchTool()],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)


# --- Writer ---

class Report(BaseModel):
    content: str

writer = Agent(
    name="Writer",
    instructions="""
    Write a detailed research report (1000+ words).
    Use markdown formatting.
    """,
    model="gpt-4o-mini",
    output_type=Report,
)


# --- Evaluator ---

class Evaluation(BaseModel):
    is_sufficient: bool
    feedback: str

evaluator = Agent(
    name="Evaluator",
    instructions="""
    Evaluate if the research report is complete and detailed.
    If not, explain what is missing.
    """,
    model="gpt-4o-mini",
    output_type=Evaluation,
)


# --- Clarifier ---

class ClarificationOutput(BaseModel):
    questions: list[str]

clarifier = Agent(
    name="Clarifier",
    instructions="""
    Given a research query, generate 2-3 clarifying questions if needed.
    Keep them short and useful.
    """,
    model="gpt-4o-mini",
    output_type=ClarificationOutput,
)


# --- Refiner ---

refiner = Agent(
    name="Refiner",
    instructions="""
    Improve the research query based on missing information.
    Make it more specific.
    """,
    model="gpt-4o-mini",
)
