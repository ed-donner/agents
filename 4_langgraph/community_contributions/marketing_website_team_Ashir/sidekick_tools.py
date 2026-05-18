"""
Tools setup for the Marketing Website Team sidekick.

Local copy of the standard Sidekick tools so this project can run
standalone (Playwright browser, Serper search, file tools, Python REPL, etc.).
"""

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain.tools import StructuredTool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from pathlib import Path


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
    requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text},
    )
    return "success"


def get_file_tools():
    # Ensure sandbox directory exists
    sandbox_dir = Path(__file__).parent / "sandbox"
    sandbox_dir.mkdir(exist_ok=True)
    toolkit = FileManagementToolkit(root_dir=str(sandbox_dir))
    return toolkit.get_tools()


def save_file(content: str, filename: str) -> str:
    """
    Save content to a file in the sandbox directory.
    Supports any file type based on the extension (e.g., .md, .html, .py, .txt, .json, .csv, etc.).

    You MAY include subdirectories in the filename (e.g., "backend/app.py",
    "frontend/src/App.tsx"); missing parent directories will be created.
    """
    sandbox_dir = Path(__file__).parent / "sandbox"
    sandbox_dir.mkdir(exist_ok=True)

    file_path = sandbox_dir / filename

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully saved file to: {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Use this tool when you want to send a push notification to the user",
    )

    file_tools = get_file_tools()

    # Structured tool so the model can pass both content and filename.
    save_file_tool = StructuredTool.from_function(
        save_file,
        name="save_file",
        description=(
            "Save content to a file in the sandbox directory. "
            "Takes two arguments: content (string) and filename (string, may include subdirectories "
            'like "backend/app.py" or "frontend/src/App.tsx").'
        ),
    )

    tool_search = Tool(
        name="search",
        func=serper.run,
        description=(
            "Use this tool to search the internet for information that requires current data. "
            "It returns titles, snippets, and URLs which you can then open with browser tools."
        ),
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()

    return file_tools + [push_tool, save_file_tool, tool_search, python_repl, wiki_tool]


__all__ = ["playwright_tools", "other_tools"]