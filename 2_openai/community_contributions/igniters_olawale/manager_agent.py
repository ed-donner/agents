from agents import Agent, ModelSettings

from planner_agent import planner_agent_tool
from search_agent import search_agent_tool
from writer_agent import writer_agent_tool
from email_agent import email_agent
from config import model

INSTRUCTIONS = """You are the research manager. You are given the original research query and the user's answers to the 3 clarifying questions.

Do the following in order:
1. Use search_planner_tool with the query and clarification answers to plan searches.
2. For each suggested search term, use search_tool to get a summary. Run all searches.
3. Use writing_tool with the query, clarification answers, and all search summaries to write the report.
4. Hand off to the Email agent with the full markdown report so they can format and send it.
5. After the handoff, output the full markdown report again so the user can see it.

You must use your tools; do not invent content yourself. Hand off exactly once to the Email agent with the complete report. Your final response must be the full markdown report."""

manager_agent = Agent(
    name="Manager agent",
    instructions=INSTRUCTIONS,
    tools=[planner_agent_tool, search_agent_tool, writer_agent_tool],
    handoffs=[email_agent],
    model=model,
    model_settings=ModelSettings(tool_choice="required"),
)
