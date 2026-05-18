from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import Tool
from dotenv import load_dotenv
import os
import requests

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user  = os.getenv("PUSHOVER_USER")
pushover_url   = "https://api.pushover.net/1/messages.json"
serper         = GoogleSerperAPIWrapper()


async def playwright_tools():
    """
    Launches a Playwright Chromium browser and returns:
        - list of browser tools (navigate, click, read page, etc.)
        - browser instance  (needed for cleanup)
        - playwright instance (needed for cleanup)
    """
    playwright = await async_playwright().start()
    browser    = await playwright.chromium.launch(headless=False)
    toolkit    = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    tools      = toolkit.get_tools()
    return tools, browser, playwright


def get_file_tools():
    """
    File management tools scoped to the sandbox/ directory.
    Agent can read, write, list, copy, move, and delete files.
    sandbox/ keeps all agent file activity isolated from your project.
    """
    os.makedirs("sandbox", exist_ok=True)   # ensure sandbox exists
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


def push(text: str) -> str:
    """
    Send a push notification to the user's phone via Pushover.
    Use this when a long-running task completes or needs attention.
    Requires PUSHOVER_TOKEN and PUSHOVER_USER in .env
    """
    if not pushover_token or not pushover_user:
        return "Push notification skipped — PUSHOVER_TOKEN or PUSHOVER_USER not set"

    response = requests.post(
        pushover_url,
        data={
            "token":   pushover_token,
            "user":    pushover_user,
            "message": text,
        }
    )
    return "success" if response.status_code == 200 else f"failed: {response.status_code}"


async def other_tools():
    """
    Returns all non-browser tools:
        - send_push_notification : notify user's phone
        - file tools             : read/write files in sandbox/
        - search                 : Google search via Serper API
        - python_repl            : execute Python code
        - wikipedia              : look up factual information
    """

    # Push notification
    push_tool = Tool(
        name        = "send_push_notification",
        func        = push,
        description = "Use this to send a push notification to the user's phone. "
                      "Useful when a long task completes or you need to alert the user."
    )

    file_tools = get_file_tools()

    search_tool = Tool(
        name        = "search",
        func        = serper.run,
        description = "Use this to search the web via Google. "
                      "Useful for finding current information, news, prices, or anything not on a specific website."
    )

    wikipedia      = WikipediaAPIWrapper()
    wikipedia_tool = WikipediaQueryRun(
        api_wrapper = wikipedia,
        description = "Use this to look up factual information on Wikipedia. "
                      "Good for definitions, historical facts, and general knowledge."
    )

    python_repl = PythonREPLTool(
        description = "Use this to execute Python code. "
                      "Useful for calculations, data processing, generating files, or anything requiring computation. "
                      "Always include a print() statement to see the output."
    )

    return file_tools + [push_tool, search_tool, python_repl, wikipedia_tool]