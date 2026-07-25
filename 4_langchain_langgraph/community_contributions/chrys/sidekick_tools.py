"""Tools for chrys sidekick: Playwright, search (optional), Wikipedia, Python REPL, sandbox files."""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

load_dotenv(override=True)

_CHRYS_DIR = Path(__file__).resolve().parent
SANDBOX_DIR = _CHRYS_DIR / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

SERPER_AVAILABLE = bool(os.getenv("SERPER_API_KEY"))
if SERPER_AVAILABLE:
    serper = GoogleSerperAPIWrapper()
else:
    serper = None


def _playwright_headless() -> bool:
    return os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("1", "true", "yes")


async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=_playwright_headless())
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    if not pushover_token or not pushover_user:
        return "pushover not configured"
    requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text},
        timeout=30,
    )
    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir=str(SANDBOX_DIR))
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification",
    )
    file_tools = get_file_tools()
    tools = file_tools + [push_tool]

    if SERPER_AVAILABLE and serper is not None:
        tool_search = Tool(
            name="search",
            func=serper.run,
            description="Use this tool when you want to get the results of an online web search",
        )
        tools.append(tool_search)

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    python_repl = PythonREPLTool()
    tools.extend([wiki_tool, python_repl])
    return tools


def serper_warning_message() -> str | None:
    if SERPER_AVAILABLE:
        return None
    return (
        "SERPER_API_KEY is not set — the `search` tool is disabled. "
        "Add the key to your environment to enable web search."
    )
