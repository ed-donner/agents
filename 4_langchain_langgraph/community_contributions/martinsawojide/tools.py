import asyncio
import os

from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain_core.tools import tool

load_dotenv(override=True)


@tool
async def lookup_wikipedia(query: str) -> str:
    """Look up technical terminology, component descriptions, or process definitions
    before proposing hypotheses."""
    wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000)
    return await asyncio.to_thread(wrapper.run, query)


@tool
async def search_failure_modes(query: str) -> str:
    """Search the web for known failure modes, root causes, and technical
    information relevant to the current hypothesis or phenomenon.
    Input should be a focused search query."""
    wrapper = GoogleSerperAPIWrapper(k=5)
    return await asyncio.to_thread(wrapper.run, query)


@tool
async def search_recent_failures(query: str) -> str:
    """Search recent news and incident reports for real-world failure events
    and occurrences related to the current hypothesis or phenomenon.
    Input should be a focused search query."""
    wrapper = GoogleSerperAPIWrapper(k=5, type="news")
    return await asyncio.to_thread(wrapper.run, query)


@tool
async def search_engineering_papers(query: str) -> str:
    """Search academic and engineering literature — IEEE papers, FMEA studies,
    reliability engineering references — for technical root cause evidence.
    Input should be a focused search query."""
    wrapper = GoogleSerperAPIWrapper(k=3, type="scholar")
    return await asyncio.to_thread(wrapper.run, query)


async def investigation_tools() -> list:
    """Return tools available to the why_generator node.

    Serper web search tools are included only when SERPER_API_KEY is set;
    the agent falls back to Wikipedia-only hypothesis generation otherwise.
    """
    if os.getenv("SERPER_API_KEY"):
        return [
            search_failure_modes,
            search_recent_failures,
            search_engineering_papers,
            lookup_wikipedia,
        ]
    return [lookup_wikipedia]
