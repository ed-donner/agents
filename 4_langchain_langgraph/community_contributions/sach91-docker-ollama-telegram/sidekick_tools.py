from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os, socket
import requests
# from langchain.agents import Tool
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
# from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from ddgs import DDGS
from typing import List, Dict
from dockertool import PythonREPLDockerTool


load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
# serper = GoogleSerperAPIWrapper()

telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
telegram_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
telegram_sync = False

try:
    print("Telegram DNS:", socket.gethostbyname_ex("api.telegram.org"))  # will raise if blocked
    telegram_sync = True
except:
    print("Telegram DNS blocked")

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


# def push(text: str):
#     """Send a push notification to the user"""
#     requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
#     return "success"

def push(message: str):
    """Send a push notification to the user via telegram"""
    if telegram_sync:
        print(f"Push Sync: {message}")
        payload = {"chat_id": telegram_chat_id, "text": message}
        response = requests.post(telegram_url, json=payload)
        return response.json()
    else:
        print(f"Message not sent: {message}")
        return {"ok": True}

def web_search(query: str, safe_search: str = "moderate") -> List[Dict[str, str]]:
    """
    Search the web with DuckDuckGo and return up the results.
    safe_search: "off" | "moderate" | "strict"
    """
    max_results = 1
    print('Web search Query ->', query)
    results: List[Dict[str, str]] = []
    # ddg regions: "wt-wt" is worldwide; you can add region=... if you want localization
    with DDGS() as ddgs:
        for r in ddgs.text(query, safesearch=safe_search, max_results=max_results):
            results.append({
                "title": r.get("title") or "",
                "url": r.get("href") or r.get("url") or "",
                "snippet": r.get("body") or r.get("snippet") or ""
            })
    print('Web search result ->', results)
    return results


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search = Tool(
        name="search",
        func=web_search,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLDockerTool() # PythonREPLTool()

    return file_tools + [push_tool, tool_search, python_repl, wiki_tool]

