import asyncio
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from agents import Agent, Runner


load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


from langchain_experimental.tools import PythonREPLTool
from pydantic import Field
import os

class SandboxPythonREPLTool(PythonREPLTool):
    sandbox_path: str = Field(default="./sandbox", description="Directory to run REPL code in")

    def _run(self, query: str) -> str:
        """Run synchronously, changing cwd to sandbox."""
        old_cwd = os.getcwd()
        try:
            os.chdir(os.path.abspath(self.sandbox_path))
            return super()._run(query)
        finally:
            os.chdir(old_cwd)

    async def _arun(self, query: str) -> str:
        """Run asynchronously — just wraps the sync method."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, query)

code_review_agent = Agent(
    name="Code Review Agent",
    instructions="""You are an expert code reviewer. Your job is to review code for:
    - Code quality and best practices
    - Potential bugs and edge cases
    - Performance issues
    - Security vulnerabilities
    - Readability and maintainability (follow PEP 8 guidelines)
    - Proper error handling
    - Ensure type hinting and proper documentation is included
    
    You should return the code with the improvements as your final output.""",
    model="gpt-4o-mini",
)
    
async def review_code_async(code: str) -> str:
    """Review code using the code review agent."""
    result = await Runner.run(code_review_agent, f"Please review this code:\n\n{code}")
    return result.final_output  # or however you extract the response
def review_code_sync(code: str) -> str:
    """Sync wrapper - not used in async context."""
    return "Use async version"


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = SandboxPythonREPLTool(sandbox_path="./sandbox")
    python_repl.description += (
        " It can also use subprocess and 'uv run' commands for shell operations."
        """ You can check the list of installed packages doing "import subprocess; subprocess.run(['uv', 'pip' 'list'])" """
        "Use installed packages before adding new ones with uv add package-name." 
        "For example, use Plotly for visualizations and pandas for data analysis."
    )

    code_review_tool = Tool(
        name="code_review",
        func=review_code_sync,
        coroutine=review_code_async,
        description="Use this tool to review code quality, identify bugs, security issues, and get suggestions for improvement. Pass the code as a string."
    )

    return file_tools + [push_tool, tool_search, python_repl,  wiki_tool, code_review_tool]

