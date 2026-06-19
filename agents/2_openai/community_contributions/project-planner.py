"""
a project planner for Productivity Tracker - Multi-Agent Development Workflow

This script demonstrates a multi-agent system for a mini project development workflow:
1. Sales Guy: Collects requirements and creates feature list
2. Manager: Breaks down features into tasks
3. Senior Dev: Analyzes technical difficulties and solutions
4. CTO: Creates final summary and sends email to CEO

The workflow uses handoffs to transfer control between agents, creating a realistic
development team simulation.
"""

import resend
import os
import asyncio
from typing import Dict
from agents import Runner, Agent, OpenAIChatCompletionsModel, function_tool, set_default_openai_client, set_tracing_disabled

from openai import AsyncOpenAI

# Initialize email service API key
resend.api_key = os.getenv("RESEND_API_KEY")
print(resend.api_key)

# Configure custom OpenAI client for DeepSeek model
custom_client = AsyncOpenAI(
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
set_default_openai_client(custom_client)
set_tracing_disabled(True)


# Agent 1: Markdown to HTML Converter
# This agent converts markdown text to HTML format for email sending
markdown_to_html = Agent(
  name="Markdown to HTML",
  instructions="""You are a markdown to html converter. \
  You are given a markdown text and you need to convert it to an html text. """,
  model=OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=custom_client
  )
)
# Convert the agent to a tool so it can be used by other agents
markdown_to_html_tool = markdown_to_html.as_tool(tool_name="markdown_to_html", tool_description="Convert a markdown text to an html text")


# Tool: Email Sender Function
# This function sends emails using the Resend service
@function_tool
def send_email(html_body: str) -> Dict[str, str]:
  """
  Sends an email with the given subject and HTML body.
  
  Args:
      subject: Email subject line
      html_body: HTML content of the email
  
  Returns:
      Dict containing status and email body
  """
  params: resend.Emails.SendParams = {
      "from": "Acme <onboarding@resend.dev>",
      "to": ["xxxx@example.com"],
      "subject": "project proposal",
      "html": html_body
  }

  email = resend.Emails.send(params)
  print(email)

  return { "status": "success", "email_body": html_body }

# Agent 4: CTO (Chief Technology Officer)
# Final agent that reviews everything and sends summary email to CEO
CTO = Agent(
  name="CTO",
  instructions="""You are a CTO who can review the project proposal and the list of features as well as the estimated time required to complete each feature as well as the technical difficulties and the solutions to avoid them. \
    you will make comprehensive and concrete summary of the project implemnation plan in markdown format and use the tools like markdown_to_html and html_send_email to send the summary to CEO.
    IMPORTANT: plz don't ask for additional details or say "let me know if you'd like to proceed" - just SEND THE SUMMARY EMAIL to CEO.
    """,
  tools=[markdown_to_html_tool, send_email],  # Has access to markdown conversion and email sending tools
  model=OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=custom_client
  )  
)  

# Agent 3: Senior Developer
# Analyzes technical difficulties and solutions, then hands off to CTO
senior_dev = Agent(
  name="Senior Dev",
  instructions="""You are a senior developer and now both the front end and back end developers are working on the same project. \
  base on your expertice in this field, you need to see what might have happen precautiously and you need to help the developers to avoid these issues. \
  so you need to write down the technological difficulties and the solutions to avoid them. \
  IMPORTANT: After analyzing the technical difficulties and solutions, you MUST handoff the result from Manager and your's analysis to CTO. \
  Do not just respond with text - actually perform the handoff.""",
  model=OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=custom_client
  ),
  handoffs=[CTO]  # Can handoff to CTO for final review
) 

# Agent 2: Manager
# Breaks down features into tasks and assigns them to developers
manager = Agent(
  name="Manager",
  instructions="""You are a manager who can assign tasks to developers. \
  You are given a list of features for an project proposal and you need to break them down into a list of task. \
  IMPORTANT: After breaking down the features into tasks, you MUST handoff to senior_dev \
  based on the nature of the tasks. Do not just respond with text - actually perform the handoff.""",
  model=OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=custom_client
  ),
  handoffs=[senior_dev]  # Can handoff to senior developer for technical analysis
)

# Agent 1: Sales Guy
# Initial agent that collects requirements and creates feature list
sales_guy = Agent(
  name="Sales Guy",
  instructions="""You are a sales guy who can sell a web application. 
  You have collected a list of customers needs and you want to communicate with the tech guys in your company to build a new web application.
  You will make a list of features the application should have and handoff to manager. 
  CRITICAL: After you have created the list of features, you MUST immediately handoff to manager. \
  Do not ask for additional details or say "let me know if you'd like to proceed" - just handoff to manager right after creating the feature list.""",
  model=OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=custom_client
  ),
  handoffs=[manager]  # Can handoff to manager for task breakdown
)


# Main execution function
async def main():
  """
  Main function that initiates the multi-agent workflow.
  
  The workflow follows this sequence:
  1. Sales Guy: Creates feature list from requirements
  2. Manager: Breaks down features into tasks
  3. Senior Dev: Analyzes technical difficulties and solutions
  4. CTO: Creates final summary and sends email to CEO
  """
  result = await Runner.run(sales_guy, """
    I have collected a list of customers needs and I want to communicate with the tech guys in my company to build a new web application.
    the project proposal is to build a GTD Productivity Tracker.
    the list feature it should have are: 
    - beign able to talk to an AI assitant to input task and get task list
    - automatically sync the task to Google Calader
    - add a review section each day 18:15 to user to review the task and get task list
    - a personal dashboard which will sycn up with Notion
  """)
  print(result)

# Entry point - run the main function when script is executed
if __name__ == "__main__":
  asyncio.run(main())
