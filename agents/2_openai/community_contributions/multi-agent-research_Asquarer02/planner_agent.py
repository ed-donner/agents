from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 3

INSTRUCTIONS = (
    "You are a research planning expert. Given a research query and the answers to clarifying questions, "
    "you will generate a set of targeted web searches to gather comprehensive information.\n\n"
    "Your task is to:\n"
    "1. Analyze the original query and clarification answers\n"
    "2. Identify key aspects and subtopics to research\n"
    "3. Generate specific search queries that will yield the most relevant information\n"
    "4. Ensure the searches cover different angles and perspectives\n\n"
    f"Output exactly {HOW_MANY_SEARCHES} search queries that will best answer the research needs."
)

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query")
    query: str = Field(description="The search term to use for the web search")
    expected_focus: str = Field(description="What specific aspect of the research this search will help with")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query")
    overall_strategy: str = Field(description="Brief explanation of the overall search strategy")

planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
) 