from pathlib import Path
import os
import subprocess
import sys
from typing import Optional
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
try:
    from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
    PLAYWRIGHT_TOOLKIT_AVAILABLE = True
except ImportError:
    PlayWrightBrowserToolkit = None
    PLAYWRIGHT_TOOLKIT_AVAILABLE = False
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
try:
    from langchain_experimental.tools import PythonREPLTool
except ImportError:
    PythonREPLTool = None
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False
import requests


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR.parent / "data"
TASKS_ROOT = PROJECT_DIR / "tasks"
load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()


async def playwright_tools():
    """Return playwright tools if available, otherwise return empty tools."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Warning: Playwright not installed. Browser tools will be unavailable.")
        print("To enable browser tools, install playwright: pip install playwright && playwright install")
        return [], None, None
    
    if not PLAYWRIGHT_TOOLKIT_AVAILABLE or PlayWrightBrowserToolkit is None:
        print("Warning: PlayWrightBrowserToolkit not available. Browser tools will be unavailable.")
        return [], None, None
    
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright
    except Exception as e:
        print(f"Warning: Playwright tools unavailable: {e}")
        print("To enable browser tools, run: playwright install")
        return [], None, None


def push(text: str):
    """Send a push notification to the user."""
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools(workspace_dir: Optional[str] = None):
    """Get file management tools scoped to a specific workspace directory."""
    if workspace_dir:
        workspace_path = Path(workspace_dir).resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)
        toolkit = FileManagementToolkit(root_dir=str(workspace_path))
    else:
        TASKS_ROOT.mkdir(parents=True, exist_ok=True)
        toolkit = FileManagementToolkit(root_dir=str(TASKS_ROOT))
    return toolkit.get_tools()


# _make_validator_tool removed - no longer using JSON validator


async def other_tools(workspace_dir: Optional[str] = None):
    """
    Get tools for the agent.

    Args:
        workspace_dir: Optional workspace directory to scope file tools
    """
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification to the user",
    )
    file_tools = get_file_tools(workspace_dir)

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search",
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    tools = [push_tool, tool_search, wiki_tool]
    
    if PythonREPLTool is not None:
        python_repl = PythonREPLTool()
        tools.append(python_repl)

    return file_tools + tools

