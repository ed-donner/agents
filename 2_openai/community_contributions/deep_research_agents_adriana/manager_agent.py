from agents import Agent, Runner, trace, gen_trace_id, function_tool
from pydantic import BaseModel, Field

from search_agent import search_tool
from clarifier_agent import clarify_tool
from answer_agent import answer_tool
from planner_agent import planner_tool, WebSearchItem, WebSearchPlan
from report_agent import report_tool, ReportData
from eval_agent import eval_tool, Evaluation
from email_agent import email_agent

import asyncio

import os
from dotenv import load_dotenv

load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')


tools = [search_tool, clarify_tool, answer_tool, planner_tool, report_tool, eval_tool]
handoffs =[email_agent]



class EmailOut(BaseModel):
    subject: str
    body_html: str
    markdown_report: str


INSTRUCTIONS = """You are the orchestrator for a multi-step research workflow.
Use the provided tools for planning, searching, writing, and evaluation, and delegate the email sending via the provided handoff agent. 
Never invent tool outputs. 
If a tool fails or returns invalid data, retry once with the same arguments.

Follow the steps carefully:
1. Call the clarify tool to obtain 3 clarifying questions. 
   
2. Call the answer tool to obtain the answers for the provided questions.

3. Call the planner tool to get a WebSearchPlan.

4. For each plan item, call the search tool with the item's search term.

5. Call the report tool with the original query and a compact list of all search summaries.

6. Evaluate the report and give feedback if necessary.

7. Handoff to email_agent with the final report so it generates a subject, 
converts to clean HTML, sends the email, and returns subject and html_body;. 

You MUST use all of the tools and handoffs provided to you. """


manager_agent = Agent(
    name = 'ManagerAgent',
    instructions = INSTRUCTIONS,
    tools = tools,
    handoffs = handoffs,
    model = 'gpt-4o-mini',
    output_type = EmailOut,

)