import os
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit, FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import Tool
from dotenv import load_dotenv

load_dotenv(override=True)

# ── env ──────────────────────────────────────────────────────────────────────
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
github_token = os.getenv("GITHUB_TOKEN")
serper = GoogleSerperAPIWrapper()

SANDBOX_DIR = Path(__file__).parent / "sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)

MEMORY_DB = str(Path(__file__).parent / "sidekick_memory.db")


# ── playwright (browser) ─────────────────────────────────────────────────────
async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


# ── push notification ─────────────────────────────────────────────────────────
def push(text: str) -> str:
    """Send a push notification to Chidera's phone via Pushover."""
    if not pushover_token or not pushover_user:
        return "Pushover credentials not set — skipping push notification"
    requests.post(pushover_url, data={
        "token": pushover_token,
        "user": pushover_user,
        "message": text,
    })
    return "Push notification sent"


# ── file management ───────────────────────────────────────────────────────────
def get_file_tools():
    toolkit = FileManagementToolkit(root_dir=str(SANDBOX_DIR))
    return toolkit.get_tools()


# ── web search ────────────────────────────────────────────────────────────────
def get_search_tool():
    return Tool(
        name="search",
        func=serper.run,
        description="Search the web. Use for current events, technical docs, package info, anything that needs up-to-date information.",
    )


# ── wikipedia ─────────────────────────────────────────────────────────────────
def get_wikipedia_tool():
    return WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())


# ── python repl ───────────────────────────────────────────────────────────────
def get_python_repl():
    return PythonREPLTool()


# ── GitHub ────────────────────────────────────────────────────────────────────
def github_search_repos(query: str) -> str:
    """
    Search GitHub repositories by keyword.
    Returns the top 5 results with name, stars, and description.
    Example input: "react micro-frontends typescript"
    """
    if not github_token:
        return "GITHUB_TOKEN not configured in .env — cannot search GitHub"
    try:
        from github import Github, GithubException
        g = Github(github_token)
        repos = g.search_repositories(query=query, sort="stars", order="desc")
        results = []
        for repo in list(repos)[:5]:
            results.append(
                f"- {repo.full_name} ⭐{repo.stargazers_count}: {repo.description or 'No description'}"
            )
        return "\n".join(results) if results else "No repositories found"
    except Exception as e:
        return f"GitHub search error: {e}"


def github_read_file(repo_and_path: str) -> str:
    """
    Read the contents of a file from a GitHub repository.
    Format: owner/repo:path/to/file
    Example: vercel/next.js:packages/next/README.md
    """
    if not github_token:
        return "GITHUB_TOKEN not configured in .env"
    if ":" not in repo_and_path:
        return "Input must be in the format: owner/repo:path/to/file"
    try:
        from github import Github, GithubException
        repo_name, file_path = repo_and_path.split(":", 1)
        g = Github(github_token)
        repo = g.get_repo(repo_name.strip())
        contents = repo.get_contents(file_path.strip())
        text = contents.decoded_content.decode("utf-8")
        if len(text) > 4000:
            text = text[:4000] + "\n\n[...truncated — file exceeds 4000 chars]"
        return text
    except Exception as e:
        return f"GitHub read error: {e}"


def github_list_issues(repo_and_filter: str) -> str:
    """
    List open issues from a GitHub repository.
    Format: owner/repo or owner/repo:label
    Example: facebook/react or facebook/react:bug
    """
    if not github_token:
        return "GITHUB_TOKEN not configured in .env"
    try:
        from github import Github
        label = None
        if ":" in repo_and_filter:
            repo_name, label = repo_and_filter.split(":", 1)
        else:
            repo_name = repo_and_filter
        g = Github(github_token)
        repo = g.get_repo(repo_name.strip())
        kwargs = {"state": "open"}
        if label:
            kwargs["labels"] = [label.strip()]
        issues = list(repo.get_issues(**kwargs))[:8]
        if not issues:
            return "No open issues found"
        return "\n".join([f"#{i.number}: {i.title} ({i.html_url})" for i in issues])
    except Exception as e:
        return f"GitHub issues error: {e}"


# ── persistent memory ─────────────────────────────────────────────────────────
def _init_memory_db():
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            saved_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_memory(key_value: str) -> str:
    """
    Save a fact or preference to persistent memory so it can be recalled later.
    Format: key|value
    Example: "preferred_test_runner|Vitest for new projects, Jest for existing ones"
    These memories persist across sessions.
    """
    if "|" not in key_value:
        return "Format must be key|value (use a pipe character to separate them)"
    key, value = key_value.split("|", 1)
    _init_memory_db()
    conn = sqlite3.connect(MEMORY_DB)
    conn.execute(
        "INSERT OR REPLACE INTO memories (key, value, saved_at) VALUES (?, ?, ?)",
        (key.strip(), value.strip(), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return f"Remembered: '{key.strip()}' = '{value.strip()}'"


def recall_memory(key: str) -> str:
    """
    Recall a previously saved fact from persistent memory.
    Example input: "preferred_test_runner"
    """
    _init_memory_db()
    conn = sqlite3.connect(MEMORY_DB)
    row = conn.execute(
        "SELECT value, saved_at FROM memories WHERE key = ?", (key.strip(),)
    ).fetchone()
    conn.close()
    if row:
        return f"{key.strip()}: {row[0]}  (saved {row[1][:10]})"
    return f"Nothing stored for '{key.strip()}'"


def list_memories(_: str = "") -> str:
    """
    List all facts stored in persistent memory.
    No input required.
    """
    _init_memory_db()
    conn = sqlite3.connect(MEMORY_DB)
    rows = conn.execute(
        "SELECT key, value, saved_at FROM memories ORDER BY saved_at DESC"
    ).fetchall()
    conn.close()
    if not rows:
        return "No memories stored yet"
    return "\n".join([f"• {r[0]}: {r[1]}  ({r[2][:10]})" for r in rows])


# ── assemble all tools ────────────────────────────────────────────────────────
async def other_tools():
    tools = []

    # push notification
    tools.append(Tool(
        name="send_push_notification",
        func=push,
        description="Send a push notification to Chidera's phone. Use this when a long task completes.",
    ))

    # web search
    tools.append(get_search_tool())

    # wikipedia
    tools.append(get_wikipedia_tool())

    # python repl
    tools.append(get_python_repl())

    # file management
    tools.extend(get_file_tools())

    # github
    tools.append(Tool(
        name="github_search_repos",
        func=github_search_repos,
        description="Search GitHub repositories. Input: a search query string. Returns top 5 repos with stars and descriptions.",
    ))
    tools.append(Tool(
        name="github_read_file",
        func=github_read_file,
        description="Read a file from a GitHub repo. Input format: owner/repo:path/to/file",
    ))
    tools.append(Tool(
        name="github_list_issues",
        func=github_list_issues,
        description="List open issues from a GitHub repo. Input: owner/repo or owner/repo:label",
    ))

    # persistent memory
    tools.append(Tool(
        name="save_memory",
        func=save_memory,
        description="Save a fact to persistent memory that will be available in future sessions. Format: key|value",
    ))
    tools.append(Tool(
        name="recall_memory",
        func=recall_memory,
        description="Retrieve a previously saved fact from persistent memory. Input: the key name.",
    ))
    tools.append(Tool(
        name="list_memories",
        func=list_memories,
        description="List all facts stored in persistent memory. No input needed.",
    ))

    return tools
