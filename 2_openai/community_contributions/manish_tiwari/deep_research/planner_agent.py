from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 4

CLARIFY_INSTRUCTIONS = (
    "You are a research planning assistant. Given the user's research query, output a JSON object with key "
    "`questions` (array of strings). The array MUST contain exactly 3 short, specific clarifying questions that "
    "narrow scope, timeframe, audience, geography, depth, or success criteria. "
    "Each question should be answerable in a few words or sentences. Do not answer them yourself."
)


class ClarifyingQuestions(BaseModel):
    """Model output may include 1–8 items; the manager normalizes to exactly three for the UI."""

    questions: list[str] = Field(
        min_length=1,
        max_length=8,
        description="Clarifying questions to refine the research (aim for exactly three distinct questions).",
    )


clarifying_planner_agent = Agent(
    name="ClarifyingPlannerAgent",
    instructions=CLARIFY_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)

PLAN_INSTRUCTIONS = (
    f"You are a helpful research assistant. You receive: the user's query; the user's answers to clarifying questions; "
    f"and optional feedback from a prior evaluation asking for more coverage.\n"
    f"Propose {HOW_MANY_SEARCHES} web search items. Each item must include a precise search query and a short reason. "
    "Tune queries using clarifications (timeframe, region, audience, technical level). "
    "If refinement feedback is provided, bias new searches toward the missing topics and suggested improvements. "
    "Avoid duplicating earlier search themes if refinement text lists them—explore complementary angles."
)


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query.",
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLAN_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
