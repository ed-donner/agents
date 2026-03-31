from pydantic import BaseModel, Field
from agents import Agent
from clarifying_questions_tool import clarifying_questions

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a helpful research assistant. 

Before planning any searches, you MUST first use the ask_clarifying_questions tool 
to gather more context about the user's query.

Once you have the user's answers, use them alongside the original query to come up 
with a set of web searches to perform. Output {HOW_MANY_SEARCHES} terms to query for.

STEP 1: Call the clarifying_questions tool ONCE with the user's original query. Wait for the output.
STEP 2: Using the original query AND the answers from the tool output, generate {HOW_MANY_SEARCHES} web search terms.

Do NOT call clarifying_questions more than once. Do NOT call it on the answers.
After STEP 1 completes, produce the final WebSearchPlan immediately—no further tool calls.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
    tools=[clarifying_questions],
)