from issues import IssueStore

from issues_server import add_issue, search_issues
from IPython.display import Markdown, display
import asyncio
from agents import Agent, Runner, trace

from agents.mcp import MCPServerStdio

from dotenv import load_dotenv

import logging

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

load_dotenv(override=True)

async def search_known_issues(request: str):
    instructions = """You are able to search for issues in the database.
    Always use the search_issues tool to search for issues and when responding inform the user clearly
     that they faced same issue before and the command to fix it. If no such issue is found in the database, inform the user that you are not aware of any such issue."""
    model = "gpt-4.1-mini"
    mcp_params = {"command": "uv", "args": ["run", "issues_server.py"]}

    async with MCPServerStdio(params=mcp_params, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(name="debugger-agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("debugger agent"):
            result = await Runner.run(agent, request)
        return result.final_output

async def log_terminal_activity(request: str):
    instructions = """
            You are an AI assistant responsible for documenting terminal errors so they can be traced and resolved later.

        Process:
        1. Use the read_log_file tool to read the user's terminal activity logs.
        2. Identify only issues related to errors.
        3. For each issue found:
        - Determine the error.
        - Identify the command or sequence of commands that resolved it.
        - Record the issue using the add_issue tool.
        - If multiple issues exist, call add_issue separately for each one.

        After all issues have been logged:
        - Use the clear_log tool to clear the log file.

        If no errors or issues are found in the logs:
        - Do not call add_issue.
        - Use the clear_log tool to clear the logs.
        - Inform the user that no issues were detected.
    """
    model = "gpt-4.1-mini"
    mcp_params = {"command": "uv", "args": ["run", "issues_server.py"]}
    async with MCPServerStdio(params=mcp_params, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(name="log-terminal-activity-agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("log-terminal-activity-agent"):
            result = await Runner.run(agent, request)
        return result.final_output
