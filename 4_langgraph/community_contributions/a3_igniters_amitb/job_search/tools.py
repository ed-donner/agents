from dotenv import load_dotenv

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool

load_dotenv(override=True)


async def playwright_tools():
    """
    Playwright tool for performing local headless/non-headless browser
    operations
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

async def search_tool():
    """
    Serper search tool for performing web search
    """
    serper = GoogleSerperAPIWrapper()
    tool =Tool(
        name="web_search",
        func=serper.run,
        description=(
            "Use this tool when you want to get the results of an"
            " online web search"
        )
    )
    return tool

async def add_tools():
    """
    Add tools to the assistant
    """
    tools, browser, playwright = await playwright_tools()
    tools += await search_tool()
    return tools
