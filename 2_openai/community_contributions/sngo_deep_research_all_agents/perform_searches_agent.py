from search_agents import search_agent
from pydantic import BaseModel, Field
from agents import Agent
import constants

search_agent_tool = search_agent.as_tool(tool_name="WebSearchTool", tool_description="Perform a single web search based on a query and a reason.")
perform_searches_agent = Agent(
    name="BatchSearchAgent",
    instructions=(
        "You are a search orchestrator. You receive a WebSearchPlan containing multiple search queries. "
        "For each item, call WebSearchTool to perform the search. "
        "Return a list of all results."
    ),
    model=constants.model,
    tools=[search_agent_tool]
)