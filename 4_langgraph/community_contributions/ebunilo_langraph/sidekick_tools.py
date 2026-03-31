from __future__ import annotations

import ast
import ipaddress
import operator
import os
import re
from urllib.parse import urlparse
from collections.abc import Callable
from typing import Any

import requests
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit, PlayWrightBrowserToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from playwright.async_api import async_playwright

from task_store import list_recent_tasks, save_task

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

_serper = None


def _serper_run(query: str) -> str:
    global _serper
    if _serper is None:
        try:
            _serper = GoogleSerperAPIWrapper()
        except Exception as e:
            return f"Web search unavailable (configure SERPER_API_KEY): {e}"
    try:
        return _serper.run(query)
    except Exception as e:
        return f"Search failed: {e}"


def push(text: str) -> str:
    """Send a push notification (requires PUSHOVER_TOKEN and PUSHOVER_USER)."""
    if not pushover_token or not pushover_user:
        return "Pushover not configured."
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def fetch_url_text(url: str, max_chars: int = 12000) -> str:
    """Fetch a URL and return visible text (no JS). Lighter than a full browser for static pages."""
    parsed = urlparse((url or "").strip())
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname:
        return "Blocked: only valid http/https URLs are allowed."
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return "Blocked: private, loopback, and internal network addresses are not allowed."
    except ValueError:
        lowered = hostname.lower()
        if lowered in {"localhost", "host.docker.internal"} or lowered.endswith(".local"):
            return "Blocked: localhost and internal hostnames are not allowed."
    headers = {"User-Agent": "SidekickResearchBot/1.0 (educational)"}
    resp = requests.get(url, timeout=20, headers=headers)
    resp.raise_for_status()
    raw = resp.text
    raw = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]"
    return text


def _safe_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _safe_eval(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp):
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }
        op_type = type(node.op)
        if op_type not in ops:
            raise ValueError("Operator not allowed")
        return ops[op_type](left, right)
    raise ValueError("Expression not allowed")


def calculate_math(expression: str) -> str:
    """Safely evaluate a numeric expression with + - * / ** % and parentheses. No names or calls."""
    expr = (expression or "").strip()
    if not expr:
        return "Empty expression"
    tree = ast.parse(expr, mode="eval")
    try:
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"Could not evaluate: {e}"


PYTHON_BLOCK_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+requests\b",
    r"\bfrom\s+os\s+import\b",
    r"\bfrom\s+subprocess\s+import\b",
    r"\bos\.environ\b",
    r"\bsubprocess\.",
    r"\bsocket\.",
    r"\bopen\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
    r"\bpip\s+install\b",
    r"\brm\s+-rf\b",
]


def guarded_python(code: str) -> str:
    """Run only low-risk Python snippets and block common dangerous patterns."""
    snippet = (code or "").strip()
    if not snippet:
        return "Blocked: empty Python input."
    for pattern in PYTHON_BLOCK_PATTERNS:
        if re.search(pattern, snippet, flags=re.IGNORECASE):
            return "Blocked by guardrails: unsafe Python code or system access was requested."
    python_repl = PythonREPLTool()
    try:
        return str(python_repl.run(snippet))
    except Exception as e:
        return f"Python execution failed: {e}"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def playwright_tools():
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "").lower() in ("1", "true", "yes")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def build_research_tools(username_getter: Callable[[], str]) -> list:
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    search_tool = Tool(
        name="search",
        func=_serper_run,
        description="Web search for current facts, links, and snippets (Google Serper).",
    )

    def save_my_task(title: str, summary: str = "") -> str:
        return save_task(username_getter(), title, summary or title)

    tools: list = [
        search_tool,
        wiki_tool,
        Tool(
            name="fetch_url_text",
            func=fetch_url_text,
            description="HTTP GET a URL and return plain text (good for docs, static HTML). Max ~12k chars.",
        ),
        Tool(
            name="list_my_recent_tasks",
            func=lambda _q: list_recent_tasks(username_getter()),
            description="List this user's recently saved tasks from the task library (same username as login). Pass any short query or leave blank.",
        ),
        Tool(
            name="save_task_to_library",
            func=save_my_task,
            description="Save a short title and summary of the current assignment to the user's task library for later.",
        ),
    ]
    if pushover_token and pushover_user:
        tools.append(
            Tool(
                name="send_push_notification",
                func=push,
                description="Send a push notification to the user via Pushover.",
            )
        )
    return tools


def build_files_tools(username_getter: Callable[[], str]) -> list:
    def save_my_task(title: str, summary: str = "") -> str:
        return save_task(username_getter(), title, summary or title)

    return get_file_tools() + [
        Tool(
            name="guarded_python",
            func=guarded_python,
            description="Run low-risk Python snippets for calculations or text/data transforms. Dangerous imports, file access, env access, subprocesses, and networking are blocked.",
        ),
        Tool(
            name="calculate_math",
            func=calculate_math,
            description="Evaluate a numeric expression only, e.g. '(2 + 3) * 4 ** 0.5'. No variables or functions.",
        ),
        Tool(
            name="save_task_to_library",
            func=save_my_task,
            description="Save a short title and summary of work to the user's persistent task library.",
        ),
    ]
