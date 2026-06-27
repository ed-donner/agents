from pydantic import BaseModel, Field
from agents import Agent
import parameters as param


# structure for item in output list, two fields with descriptions
class WebSearchItem(BaseModel):
    search_term: str = Field(description="A web search term that you use to respond to the query.")
    reason: str = Field(description="Your reason for choosing this search term for the query.")


# structure of output: a list of items contained in "searches" field with description
class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="The WebSearchItem objects that you created.")
    

# make sure the model spec is current
planner_agent = Agent[WebSearchPlan](
    name="PlannerAgent",
    instructions= param.INSTRUCTIONS_PLANNER,
    model= param.MODEL_PLANNER,
    output_type=WebSearchPlan,
)