"""
Shared tools for Australia Scholarship Research agents: Serper (web search) and Playwright (browser).
All agents receive both tools via LangChainToolAdapter for AutoGen.
"""

import os
from typing import List, Tuple, Any

from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from playwright.async_api import async_playwright

from autogen_ext.tools.langchain import LangChainToolAdapter

load_dotenv(override=True)


def get_serper_tool() -> LangChainToolAdapter:
    """Build Serper web search tool for AutoGen agents."""
    serper = GoogleSerperAPIWrapper()
    langchain_tool = Tool(
        name="internet_search",
        func=serper.run,
        description=(
            "Search the internet for current information. Use this to find "
            "universities, scholarships, deadlines, and official program pages. "
            "Returns titles, snippets, and URLs."
        ),
    )
    return LangChainToolAdapter(langchain_tool)


async def get_playwright_tools() -> Tuple[List[LangChainToolAdapter], Any, Any]:
    """
    Build Playwright browser tools for AutoGen agents.
    Returns (list of tool adapters, browser, playwright) so caller can close them later.
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    langchain_tools = toolkit.get_tools()
    adapters = [LangChainToolAdapter(t) for t in langchain_tools]
    return adapters, browser, playwright


def get_serper_tools_for_agents() -> List[LangChainToolAdapter]:
    """Return list of Serper-only adapters (for use when Playwright is not needed)."""
    return [get_serper_tool()]
