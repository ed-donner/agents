import ast
import operator
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from playwright.async_api import async_playwright


load_dotenv(override=True)

serper = GoogleSerperAPIWrapper()

# Sandbox relative to this package so file tools work when launched from this folder.
_SANDBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")


async def playwright_tools():
    """Return Playwright browser tools, or empty list if Chromium is not installed.

    Install browsers from the project venv: ``uv run playwright install chromium``
    Set ``SIDEKICK_PLAYWRIGHT_HEADLESS=false`` for a visible window when supported.
    """
    playwright = None
    try:
        playwright = await async_playwright().start()
        headless = os.getenv("SIDEKICK_PLAYWRIGHT_HEADLESS", "true").lower() in ("1", "true", "yes")
        browser = await playwright.chromium.launch(headless=headless)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright
    except Exception as e:
        print(
            "Playwright browser unavailable — continuing without browser tools.\n"
            f"  ({e})\n"
            "  To enable: uv run playwright install chromium\n"
            "  Visible window: SIDEKICK_PLAYWRIGHT_HEADLESS=false"
        )
        if playwright is not None:
            try:
                await playwright.stop()
            except Exception:
                pass
        return [], None, None





def get_file_tools():
    os.makedirs(_SANDBOX_DIR, exist_ok=True)
    toolkit = FileManagementToolkit(root_dir=_SANDBOX_DIR)
    return toolkit.get_tools()


_SAFE_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_SAFE_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_eval_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = _SAFE_BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported binary operator")
        return op(_safe_eval_ast(node.left), _safe_eval_ast(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError("Unsupported unary operator")
        return op(_safe_eval_ast(node.operand))
    raise ValueError("Only numeric literals and + - * / % ** are allowed")


def calculator(expression: str) -> str:
    """Evaluate a numeric arithmetic expression (digits, + - * / % **, parentheses). No variables or function calls."""
    expr = (expression or "").strip()
    if not expr:
        return "Error: empty expression"
    try:
        tree = ast.parse(expr, mode="eval")
        value = _safe_eval_ast(tree.body)
        return str(value)
    except Exception as e:
        return f"Error: {e}"


def fetch_url_text(url: str, max_chars: int = 12000) -> str:
    """HTTP GET a URL and return body text. HTML pages are stripped to main text (scripts/styles removed)."""
    u = (url or "").strip()
    if not u:
        return "Error: empty URL"
    headers = {"User-Agent": "OdinachiSidekick/1.0 (educational)"}
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            r = client.get(u, headers=headers)
            r.raise_for_status()
            content_type = (r.headers.get("content-type") or "").lower()
            raw = r.text
    except Exception as e:
        return f"Error fetching URL: {e}"

    text = raw
    if "html" in content_type or raw.lstrip().lower().startswith("<!doctype html") or "<html" in raw[:500].lower():
        try:
            soup = BeautifulSoup(raw, "lxml")
            for tag in soup(["script", "style", "noscript", "svg"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except Exception:
            text = raw

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Truncated — increase max_chars if needed]"
    return text


def get_current_time(timezone_name: str = "UTC") -> str:
    """Current date and time in IANA timezone (e.g. UTC, America/New_York, Europe/London). Falls back to UTC on bad names."""
    name = (timezone_name or "UTC").strip() or "UTC"
    try:
        tz = ZoneInfo(name)
    except Exception:
        tz = ZoneInfo("UTC")
        name = "UTC (fallback)"
    now = datetime.now(tz)
    return f"{now.strftime('%Y-%m-%d %H:%M:%S %Z')} (ISO: {now.isoformat()})"


async def other_tools():
   
    file_tools = get_file_tools()

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search",
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()

    calc_tool = Tool(
        name="calculator",
        func=calculator,
        description=(
            "Evaluate a pure arithmetic expression: numbers, + - * / % **, parentheses. "
            "Use for quick math without running full Python. Example input: (19 + 23) * 2"
        ),
    )
    fetch_tool = Tool(
        name="fetch_url_text",
        func=fetch_url_text,
        description=(
            "Download a public HTTP/HTTPS URL and return page text. Prefer for static pages; "
            "use the browser tool for heavy JavaScript sites. Input: full URL string."
        ),
    )
    clock_tool = Tool(
        name="get_current_time",
        func=get_current_time,
        description=(
            "Current local time in a named IANA timezone (default UTC). "
            "Input: timezone name like America/Los_Angeles or Europe/Berlin; empty uses UTC."
        ),
    )

    return file_tools + [
      
        tool_search,
        fetch_tool,
        calc_tool,
        clock_tool,
        python_repl,
        wiki_tool,
    ]
