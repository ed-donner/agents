from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import Tool
from dotenv import load_dotenv
import requests
import os

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
    """Send a push notification to the user's phone via Pushover."""
    response = requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text},
    )
    if response.status_code == 200:
        return "Push notification sent successfully."
    return f"Failed to send push notification: {response.status_code}"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description=(
            "Send a push notification to the user's phone. "
            "Use this when the user asks to be notified, or when a long task finishes."
        ),
    )

    file_tools = get_file_tools()

    search_tool = Tool(
        name="web_search",
        func=serper.run,
        description=(
            "Search the web for up-to-date information. "
            "Use this to look up documentation, Stack Overflow answers, GitHub issues, "
            "error messages, library APIs, or any engineering topic."
        ),
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(
        api_wrapper=wikipedia,
        description=(
            "Look up background information on a concept, technology, algorithm, or standard. "
            "Best for foundational knowledge, not cutting-edge library docs."
        ),
    )

    python_repl = PythonREPLTool(
        description=(
            "Execute Python code. Use this to test snippets, reproduce bugs, run calculations, "
            "parse data, or validate logic. Always include print() to see output."
        )
    )

    return file_tools + [push_tool, search_tool, python_repl, wiki_tool]
