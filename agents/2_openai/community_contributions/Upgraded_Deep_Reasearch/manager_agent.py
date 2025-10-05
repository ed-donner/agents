# manager_agent.py

from agents import Agent, function_tool
from clarifier_agent import clarifier_agent
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import send_email

MANAGER_INSTRUCTIONS = """
You are the Research Manager orchestrator.

1) **Clarify.** Ask the user 3 clarifying questions about their original query.
2) **Plan.** Once the user answers, call ClarifierAgent to parse those answers,
   then hand off both original query + answers to PlannerAgent to get a tuned WebSearchPlan.
3) **Search.** For each item in that plan, call SearchAgent to get summaries.
4) **Write.** Pass the collected summaries to WriterAgent to produce a full report.
5) **Email.** Use the send_email tool to deliver the report via HTML.

Make sure each handoff is explicit (you invoke the appropriate tool with the right data).
"""

manager_agent = Agent(
    name="ManagerAgent",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[
        clarifier_agent.as_tool(
            tool_name="clarifier",
            tool_description="Generate 3 clarifying questions for the query"
        ),
        planner_agent.as_tool(
            tool_name="planner",
            tool_description="Create a focused search plan given query and clarifications"
        ),
        search_agent.as_tool(
            tool_name="search",
            tool_description="Summarize web search results for a given term"
        ),
        writer_agent.as_tool(
            tool_name="writer",
            tool_description="Produce a cohesive markdown report from search summaries"
        ),
        send_email,  # function tool for sending the report via email
    ],
    model="gpt-4o-mini",
)
