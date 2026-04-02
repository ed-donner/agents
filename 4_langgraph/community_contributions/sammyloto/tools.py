"""Tools for Career Sprint: web search, sandbox files, Wikipedia, optional Python REPL, local profile read."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
# from langchain.agents import Tool
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.tools import StructuredTool
from langchain_experimental.tools import PythonREPLTool

load_dotenv(override=True)


def _sandbox_root() -> Path:
    return Path(__file__).resolve().parent / "sandbox"


def _me_dir() -> Path:
    return Path(__file__).resolve().parent / "me"


def _duckduckgo_text_search(query: str) -> str:
    """Use duckduckgo-search (pip package); avoids LangChain's DuckDuckGoSearchRun which needs extra `ddgs`."""
    try:
        from duckduckgo_search import DDGS
    except ImportError as e:
        return f"Search unavailable (install duckduckgo-search): {e}"
    lines: list[str] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(str(query).strip(), max_results=6):
                title = r.get("title") or ""
                href = r.get("href") or ""
                body = (r.get("body") or "")[:400]
                lines.append(f"{title}\n{href}\n{body}")
    except Exception as e:
        return f"DuckDuckGo search error: {e}"
    return "\n\n---\n\n".join(lines) if lines else "No results."


def build_search_tool() -> Tool:
    if os.getenv("SERPER_API_KEY"):
        serper = GoogleSerperAPIWrapper()
        return Tool(
            name="web_search",
            func=serper.run,
            description=(
                "Search the web for recent facts about a company, role, industry, or interview process. "
                "Use for verifiable information; cite what you find in your final answer."
            ),
        )
    return Tool(
        name="web_search",
        func=_duckduckgo_text_search,
        description=(
            "Search the web (DuckDuckGo) when SERPER_API_KEY is not set. "
            "Use for company and role research; results may be shorter than Serper."
        ),
    )


def read_career_profile() -> str:
    """Load optional local profile text for personalized talking points."""
    path = _me_dir() / "summary.txt"
    if not path.is_file():
        return (
            "No me/summary.txt found. Add a short bio, strengths, and target roles under "
            f"'{_me_dir()}' to personalize outputs."
        )
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:12_000]


def build_tools() -> list:
    root = _sandbox_root()
    root.mkdir(parents=True, exist_ok=True)

    file_toolkit = FileManagementToolkit(root_dir=str(root))
    file_tools = file_toolkit.get_tools()

    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_repl = PythonREPLTool()

    profile_tool = StructuredTool.from_function(
        name="read_career_profile",
        description=(
            "Read the candidate's local career profile (skills, goals, voice). "
            "Call once when tailoring pitches or outreach so outputs match their story."
        ),
        func=read_career_profile,
    )

    return [build_search_tool(), profile_tool, wiki, python_repl] + file_tools
