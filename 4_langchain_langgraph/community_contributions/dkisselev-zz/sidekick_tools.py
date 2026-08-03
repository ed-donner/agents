from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_azure_dynamic_sessions import SessionsPythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import logging

logger = logging.getLogger(__name__)

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


async def other_tools():
    logger.info("Initializing tools...")
    
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    # Initialize Azure Container
    logger.info("Initializing Azure Container...")
    pool_management_endpoint = os.getenv("AZURE_CONTAINER_ENDPOINT")
    if not pool_management_endpoint:
        logger.error("AZURE_CONTAINER_ENDPOINT environment variable is not set!")
        raise ValueError(
            "AZURE_CONTAINER_ENDPOINT environment variable is not set. "
            "Please run the setup_azure_sessions.sh script to configure Azure Container Apps."
        )
    
    logger.info(f"Using Azure endpoint: {pool_management_endpoint[:50]}...")
    python_repl = SessionsPythonREPLTool(pool_management_endpoint=pool_management_endpoint)
    logger.info(f"Python REPL tool initialized successfully")


    all_tools = file_tools + [push_tool, tool_search, python_repl, wiki_tool]
    logger.info(f"Total tools initialized: {len(all_tools)}")
    for i, tool in enumerate(all_tools):
        logger.info(f"   {i+1}. {tool.name}")
    
    return all_tools

