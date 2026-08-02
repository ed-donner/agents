from agents import Agent, WebSearchTool, ModelSettings
from pydantic import BaseModel, Field
import parameters as param


# structure of results for each search term produced by planner agent
class SearchTermResult(BaseModel):
    search_term: str = Field(description="The search term you received and used for a web search.")
    summary: str = Field(description="Summary of the websites' information for the search term.")
    source: list[str] = Field(description="The web addresses you used to write the summary.")


# structure of output: a list of items contained in "sources" field with description
class SearchResults(BaseModel):
    results: list[SearchTermResult] = Field(description="The SearchItem objects that you created for each search term.")
    

# WebSearch is "built-in" tool, a kind of permission
search_agent = Agent[SearchResults](
    name="SearchAgent",
    instructions= param.INSTRUCTIONS_SEARCH,
    tools=[WebSearchTool(search_context_size="low")],
    model= param.MODEL_SEARCH,
    model_settings=ModelSettings(tool_choice="required"),
    output_type=SearchResults,
)