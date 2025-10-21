import asyncio
from pydantic import BaseModel, Field
from agents import Agent, function_tool
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from search_agent import search_agent
from writer_agent import writer_agent
from email_agent import email_agent

# Create search_agent as a tool
searcher = search_agent.as_tool(
    tool_name="searcher", 
    tool_description="Perform web search and analysis for a given search term"
)

search_planner = planner_agent.as_tool(
    tool_name="search_planner", 
    tool_description="Generate some web searches for the research")

writer = writer_agent.as_tool(
    tool_name="writer", 
    tool_description="Generate a report from the search results")
    
email = email_agent.as_tool(
    tool_name="email", 
    tool_description="Send an email with the report")

INSTRUCTIONS = (
    "You are a research manager."
    "As input you are given a search term along with three questions, each of which may or may not have a response."
    "You will use this input to hone and focus your research." 
    "It's possible each question has no response, in which case simply ignore it." 
    "You will use a search_planner tool to generate a number of web searches based on the input."
    "You will then use the searcher tool to execute all of the searches identified by the search_planner tool."
    "You will then use the writer tool to generate a report from the search results."
    "Output the report as markdown."   
    "You will then use the email tool to send the report to the user."
)
 

tools = [search_planner, searcher, writer, email]


manager_agent = Agent(
    name="ManagerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=tools
)



