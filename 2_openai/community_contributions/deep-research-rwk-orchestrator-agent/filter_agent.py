from pydantic import BaseModel, Field
from agents import Agent
import parameters as param


# structure for item in list of sources, two fields with descriptions
class FilteredItem(BaseModel):
    summary: str = Field(description="Your summary of the information in the web addresses in source field.")
    source: list[str] = Field(description="The web addresses used for the web search.")
    order_reason: str = Field(description="Your reasoning for ranking the importance of this search.")

class FilteredResults(BaseModel):
    results: list[FilteredItem] = Field(description="The filtered results.")


filter_agent = Agent[FilteredResults](
    name="FilterAgent",
    instructions= param.INSTRUCTIONS_FILTER,
    model= param.MODEL_SEARCH,
    output_type=FilteredResults,
)