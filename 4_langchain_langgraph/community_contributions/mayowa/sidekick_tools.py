from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from playwright.async_api import async_playwright

load_dotenv(override=True)


async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


async def medical_tools():
    serper = GoogleSerperAPIWrapper()
    search_tool = Tool(
        name="web_search",
        func=serper.run,
        description=(
            "Search the web for current health guidance, symptom information, red flags, "
            "and reputable medical background information."
        ),
    )

    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_tool = PythonREPLTool()

    return [search_tool, wiki_tool, python_tool]
