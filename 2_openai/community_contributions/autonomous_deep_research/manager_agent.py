from typing import Sequence
from agents import Agent, WebSearchTool, ModelSettings

from planner_agent import planner_agent_tool
from search_agent import search_agent_tool
from writer_agent import writer_agent_tool
from evaluator_agent import eval_agent, eval_agent_tool
from email_agent import email_agent


INSTRUCTIONS = """
You are a research manager. Your goal is to generate a research report using your tools. 

Follow these steps carefully:
1. Plan searches: Use planner_agent_tool to come up with the searchs required for the given topic. 
2. Perform search: Use search_agent_tool to search for the terms recommended by the planner tool.
3. Write: Use the writer_agent_tool to write the report.
4. Evaluate: Use eval_agent_tool to evaluate the research report. If the report is not acceptable then start the process by planning the searches again. Repeat the process until you find an acceptable research report.
5. Handoff for sending: Pass the generated report to 'Email agent'. The Email agent will take care of formatting and sending. 

Crucial Rules:
- You must use the tools given to you — do not generate anything yourself.
- You must hand off exactly ONE email to the Email agent — never more than one.
"""

manager_agent = Agent(
    name="Manager agent",
    instructions=INSTRUCTIONS,
    tools=[planner_agent_tool, search_agent_tool, writer_agent_tool, eval_agent_tool],
    handoffs=[email_agent],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)
