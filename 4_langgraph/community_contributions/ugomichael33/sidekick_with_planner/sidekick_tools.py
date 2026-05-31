import os
import requests
from dotenv import load_dotenv

from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper

from config import ENABLE_BROWSER

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"


async def playwright_tools():
    if not ENABLE_BROWSER:
        return [], None, None

    try:
        from playwright.async_api import async_playwright
        from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
    except Exception:
        return [], None, None

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    if not (pushover_token and pushover_user):
        return "Pushover not configured"
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    os.makedirs("sandbox", exist_ok=True)
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification",
    )
    file_tools = get_file_tools()

    serper_api_key = os.getenv("SERPER_API_KEY")
    if serper_api_key:
        serper = GoogleSerperAPIWrapper(serper_api_key=serper_api_key)
        tool_search = Tool(
            name="search",
            func=serper.run,
            description="Use this tool when you want to get the results of an online web search",
        )
        search_tools = [tool_search]
    else:
        search_tools = []

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()

    return file_tools + [push_tool, python_repl, wiki_tool] + search_tools
