from agents import Agent

from config import DEFAULT_MODEL
from planner_agent import planner_agent
from reviewer_agent import reviewer_agent
from search_agent import search_agent
from search_tuner_agent import search_tuner_agent
from writer_agent import writer_agent

# Agents-as-tools: the manager can call these directly.
tune_search_tool = search_tuner_agent.as_tool(
    tool_name="tune_search_tool",
    tool_description="Tune strategy and search depth from query and clarification answers.",
)

plan_searches_tool = planner_agent.as_tool(
    tool_name="plan_searches_tool",
    tool_description="Create a targeted web search plan from the tuned brief.",
)

run_web_search_tool = search_agent.as_tool(
    tool_name="run_web_search_tool",
    tool_description="Execute one web search query and summarize findings.",
)

MANAGER_INSTRUCTIONS = """
You are the ManagerAgent orchestrating deep research.

You must follow this process:
1) Use tune_search_tool with query + clarifications to produce a tuned brief.
2) Use plan_searches_tool using the tuned brief to produce searches.
3) Execute run_web_search_tool for every planned search item.
4) Aggregate all findings into a structured research package.
5) Mandatory handoff to WriterAgent with the full package.
6) Mandatory handoff to ReviewerAgent with the writer output.
7) Return the final reviewed markdown report.

Important:
- Always respect allowed_tools and search_budget from tuned brief.
- Never skip handoffs.
- Keep the final output as markdown only.
"""


manager_agent = Agent(
    name="ManagerAgent",
    instructions=MANAGER_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    tools=[tune_search_tool, plan_searches_tool, run_web_search_tool],
    handoffs=[writer_agent, reviewer_agent],
    handoff_description="Coordinate tuning, planning, search, and writing handoffs.",
)
