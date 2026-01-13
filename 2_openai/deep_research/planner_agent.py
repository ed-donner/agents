from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 5

QUERY_INSTRUCTIONS = """You are a helpful research assistant. Given a query, come up with 3-5 follow up questions \
to ask the user that will help you better understand what they want to research."""

PLANNER_INSTRUCTIONS = f"""You are a helpful research assistant. You receive a query along with follow-up questions and the user's answers.
Based on this information, come up with a set of web searches to perform to best answer the original query.
Output {HOW_MANY_SEARCHES} terms to query for.

After creating the search plan, hand off to continue the research process."""

class FollowUpQuestions(BaseModel):
    questions: list[str] = Field(description="A list of 3-5 follow up questions to ask the user.")

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

# query_agent generates follow-up questions for the user
query_agent = Agent(
    name="QueryAgent",
    instructions=QUERY_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=FollowUpQuestions,
)

# planner_agent receives the Q&As and creates a search plan
planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
    handoff_description="Creates a web search plan based on the query and user's answers"
)