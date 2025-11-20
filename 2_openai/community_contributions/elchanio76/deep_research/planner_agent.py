from pydantic import BaseModel, Field
from agents import Agent

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")

class PlannerAgent(Agent):
    # Initialize agent with a model, instructions and number of searches
    def __init__(self, model: str, num_searches: int = 5):
        instructions = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {num_searches} terms to query for."
        
        super().__init__(
            name="PlannerAgent",
            instructions=instructions,
            model=model,
            output_type=WebSearchPlan,
        )
        self.num_searches = num_searches
        self.model = model

#planner_agent = Agent(
#    name="PlannerAgent",
#    instructions=INSTRUCTIONS,
#    model="gpt-4o-mini",
#    output_type=WebSearchPlan,
#)