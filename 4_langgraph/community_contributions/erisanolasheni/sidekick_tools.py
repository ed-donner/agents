import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
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

SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"


def _headless() -> bool:
    return os.getenv("SIDEKICK_HEADLESS", "").strip().lower() in ("1", "true", "yes")


async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=_headless())
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str) -> str:
    if not pushover_token or not pushover_user:
        return "Pushover not configured (set PUSHOVER_TOKEN and PUSHOVER_USER)."
    try:
        r = requests.post(
            pushover_url,
            data={"token": pushover_token, "user": pushover_user, "message": text},
            timeout=15,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return f"Push failed: {e}"
    return "ok"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir=str(SANDBOX_DIR))
    return toolkit.get_tools()


def http_get_text(url: str) -> str:
    limit = 12000
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Only http/https URLs with a host are allowed."
    try:
        r = requests.get(
            url.strip(),
            timeout=20,
            headers={"User-Agent": "SidekickFetch/1.0"},
        )
    except requests.RequestException as e:
        return f"Request error: {e}"
    text = r.text or ""
    if len(text) > limit:
        text = text[:limit] + f"\n… truncated ({len(r.text)} chars total)"
    return f"status={r.status_code}\n\n{text}"


def worklog_append(line: str) -> str:
    entry = line.replace("\n", " ").replace("\r", "").strip()
    if not entry:
        return "Nothing to append."
    path = SANDBOX_DIR / "worklog.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    block = f"- {ts} {entry}\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    return f"Appended to {path.name}"


def format_json_string(payload: str) -> str:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    return json.dumps(data, indent=2, ensure_ascii=False)


def list_sandbox_files(_unused: str = "") -> str:
    cap = 120
    paths: list[str] = []
    for root, dirs, files in os.walk(SANDBOX_DIR):
        dirs.sort()
        for name in sorted(files):
            full = Path(root) / name
            try:
                rel = full.relative_to(SANDBOX_DIR)
            except ValueError:
                continue
            paths.append(str(rel))
            if len(paths) >= cap:
                return "\n".join(paths) + f"\n… stopped at {cap} entries"
    return "\n".join(paths) if paths else "(empty sandbox)"


_serper_client = None


def _search_or_stub(query: str) -> str:
    global _serper_client
    if not os.getenv("SERPER_API_KEY"):
        return "Web search needs SERPER_API_KEY in the environment."
    if _serper_client is None:
        _serper_client = GoogleSerperAPIWrapper()
    return _serper_client.run(query)


async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Send a short push notification via Pushover when the user explicitly wants an alert on their device.",
    )
    file_tools = get_file_tools()
    search_tool = Tool(
        name="search",
        func=_search_or_stub,
        description="Run a web search and return summarized results.",
    )
    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_repl = PythonREPLTool()
    http_tool = Tool(
        name="fetch_url_text",
        func=http_get_text,
        description="GET a public http(s) URL and return status plus body text (truncated).",
    )
    log_tool = Tool(
        name="append_worklog",
        func=worklog_append,
        description="Append one timestamped bullet line to sandbox/worklog.md for milestones or decisions.",
    )
    json_tool = Tool(
        name="pretty_json",
        func=format_json_string,
        description="Parse a JSON string and return a formatted version; errors if invalid.",
    )
    ls_tool = Tool(
        name="list_sandbox_files",
        func=list_sandbox_files,
        description="List up to 120 files under the sandbox directory.",
    )
    return file_tools + [
        push_tool,
        search_tool,
        wiki,
        python_repl,
        http_tool,
        log_tool,
        json_tool,
        ls_tool,
    ]
