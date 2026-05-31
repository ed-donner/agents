from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import requests

from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
#from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper 


load_dotenv(override = True)
serper = GoogleSerperAPIWrapper()


async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless = False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="events")
    return toolkit.get_tools()


async def all_tools():
    file_tool = get_file_tools()
    search_tool = Tool(
        name='event_search',
        func=serper.run,
        description='Use this tool when you want to get the results of an online web search.'
    )

    #python_repl = PythonREPLTool()
    
    return file_tool +[search_tool]