from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.tools import tool  
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from typing import List, Tuple, Any
import logging

load_dotenv(override=True)
logger = logging.getLogger(__name__)

# Environment variables
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()


async def playwright_tools() -> Tuple[List[Any], Any, Any]:
    """
    Initialize Playwright browser and return available tools.
    Returns: (tools_list, browser, playwright_instance)
    """
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        tools = toolkit.get_tools()
        logger.info(f"Initialized {len(tools)} Playwright tools")
        return tools, browser, playwright
    except Exception as e:
        logger.error(f"Error initializing Playwright: {str(e)}")
        raise


@tool 
def push_notification(text: str) -> str:
    """Send a push notification to the user via Pushover"""
    try:
        response = requests.post(
            pushover_url,
            data={
                "token": pushover_token,
                "user": pushover_user,
                "message": text
            },
            timeout=5
        )
        response.raise_for_status()
        logger.info("Push notification sent successfully")
        return "Push notification sent successfully"
    except Exception as e:
        error_msg = f"Failed to send push notification: {str(e)}"
        logger.error(error_msg)
        return error_msg


def get_file_tools() -> List[Any]:
    """Get file management tools (read, write, list files)"""
    try:
        toolkit = FileManagementToolkit(root_dir="sandbox")
        tools = toolkit.get_tools()
        logger.info(f"Initialized {len(tools)} file management tools")
        return tools
    except Exception as e:
        logger.error(f"Error initializing file tools: {str(e)}")
        return []


@tool 
def search_web(query: str) -> str:
    """
    Search the internet for information using Google Serper.
    Use when you need current information, facts, or research data.
    """
    try:
        results = serper.run(query)
        logger.debug(f"Web search for '{query}' completed")
        return results
    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def other_tools() -> List[Any]:
    """
    Gather all non-browser tools for the agent.
    Includes: file operations, web search, Wikipedia, Python REPL, push notifications
    """
    tools_list = []

    # File management tools
    try:
        file_tools = get_file_tools()
        tools_list.extend(file_tools)
        logger.info(f"Added {len(file_tools)} file tools")
    except Exception as e:
        logger.error(f"Error loading file tools: {e}")

    # Web search tool (using decorator)
    try:
        tools_list.append(search_web)
        logger.info("Added web search tool")
    except Exception as e:
        logger.error(f"Error adding search tool: {e}")

    # Push notification tool (using decorator)
    try:
        tools_list.append(push_notification)
        logger.info("Added push notification tool")
    except Exception as e:
        logger.error(f"Error adding push notification tool: {e}")

    # Wikipedia tool
    try:
        wikipedia = WikipediaAPIWrapper()
        wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
        tools_list.append(wiki_tool)
        logger.info("Added Wikipedia tool")
    except Exception as e:
        logger.error(f"Error initializing Wikipedia tool: {e}")

    # Python REPL tool
    try:
        python_repl = PythonREPLTool()
        tools_list.append(python_repl)
        logger.info("Added Python REPL tool")
    except Exception as e:
        logger.error(f"Error initializing Python REPL tool: {e}")

    logger.info(f"Total tools available: {len(tools_list)}")
    return tools_list