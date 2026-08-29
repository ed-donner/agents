from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_core.tools import StructuredTool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from pydantic import BaseModel, Field
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

load_dotenv(override=True)

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

SANDBOX_ROOT = Path(__file__).resolve().parent / "sandbox"
APPLICATIONS_DIR = SANDBOX_ROOT / "applications"
APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(name: str) -> str:
    base = os.path.basename(name.strip())
    base = re.sub(r"[^\w\-_.]", "_", base)
    if not base.lower().endswith((".md", ".txt", ".json")):
        base = f"{base}.md"
    return base[:180] if len(base) > 180 else base


def _search_duckduckgo(query: str, max_results: int = 8) -> str:
    """Free web search via DuckDuckGo (no API key). Requires `ddgs` (used by langchain_community)."""
    from langchain_community.tools import DuckDuckGoSearchResults

    tool = DuckDuckGoSearchResults(num_results=max_results)
    return tool.invoke(query)


def search_web(query: str) -> str:
    """
    Search the web for jobs, companies, and news.
    Uses Google (Serper) when SERPER_API_KEY is set; otherwise DuckDuckGo (no API key).
    """
    key = (os.getenv("SERPER_API_KEY") or "").strip()
    if key:
        try:
            from langchain_community.utilities import GoogleSerperAPIWrapper

            serper = GoogleSerperAPIWrapper()
            return serper.run(query)
        except Exception as e:  # noqa: BLE001
            return f"Serper search failed: {e}. Try again or rely on DuckDuckGo by removing SERPER_API_KEY."

    try:
        return _search_duckduckgo(query)
    except ImportError as e:
        return (
            "Web search needs the `ddgs` package (LangChain DuckDuckGo integration). Run: "
            "`uv pip install ddgs`. "
            "Or use wikipedia_lookup and fetch_job_page_text with URLs."
        )
    except Exception as e:  # noqa: BLE001
        return (
            f"DuckDuckGo search failed: {e}. "
            "Use wikipedia_lookup or fetch_job_page_text with a URL the user provides."
        )


def wikipedia_lookup(query: str) -> str:
    """Look up a topic on Wikipedia (good for company background when you have no Serper key)."""
    try:
        wiki = WikipediaAPIWrapper()
        tool = WikipediaQueryRun(api_wrapper=wiki)
        return tool.invoke(query)
    except Exception as e:  # noqa: BLE001
        return f"Wikipedia lookup failed: {e}"


def fetch_job_page_text(url: str, max_chars: int = 16_000) -> str:
    """
    Fetch a public careers or job-posting URL and return cleaned visible text (truncated).
    Use for pages that block simple scraping only when allowed by the site terms.
    """
    if not url.startswith(("http://", "https://")):
        return "URL must start with http:// or https://"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; JobHuntAssistant/1.0; +https://example.local) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        out = "\n".join(lines)
        if len(out) > max_chars:
            out = out[:max_chars] + "\n\n[truncated]"
        return out or "(no text extracted)"
    except Exception as e:  # noqa: BLE001
        return f"Failed to fetch page: {e}"


class SavePackageInput(BaseModel):
    filename: str = Field(description="Filename, e.g. acme_backend_engineer.md")
    company: str = Field(description="Company name")
    role_title: str = Field(description="Target role title")
    body_markdown: str = Field(
        description="Markdown: JD summary, matched keywords, cover letter or outreach draft"
    )


def save_job_application_package(
    filename: str,
    company: str,
    role_title: str,
    body_markdown: str,
) -> str:
    """
    Save a job-hunt artifact under sandbox/applications (cover letter draft, JD summary, etc.).
    """
    fn = _safe_filename(filename)
    path = APPLICATIONS_DIR / fn
    header = f"# {role_title} @ {company}\n\n"
    path.write_text(header + body_markdown.strip(), encoding="utf-8")
    return f"Saved to applications/{fn}"


def list_job_applications() -> str:
    """List saved files in the applications folder."""
    files = sorted(APPLICATIONS_DIR.glob("*"))
    names = [p.name for p in files if p.is_file()]
    return "\n".join(names) if names else "(no files yet)"


def read_job_application_file(filename: str) -> str:
    """Read a previously saved application file by name."""
    fn = _safe_filename(filename)
    path = APPLICATIONS_DIR / fn
    if not path.is_file():
        return f"No file named {fn}"
    return path.read_text(encoding="utf-8")


def send_push_notification(message: str) -> str:
    """
    Send a short notification to the user's device via Pushover (requires PUSHOVER_TOKEN and PUSHOVER_USER in .env).
    Use when the user asks to be notified (e.g. when a draft is ready, deadline reminder, or summary ping).
    Keep body under Pushover limits (about 1024 characters); summarize if needed.
    """
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        return (
            "Pushover is not configured: set PUSHOVER_TOKEN and PUSHOVER_USER in .env "
            "(see https://pushover.net/)."
        )
    text = (message or "").strip()
    if len(text) > 1024:
        text = text[:1021] + "..."
    try:
        r = requests.post(
            PUSHOVER_API_URL,
            data={"token": token, "user": user, "message": text},
            timeout=15,
        )
        r.raise_for_status()
        return "Push notification sent successfully."
    except Exception as e:  # noqa: BLE001
        return f"Pushover request failed: {e}"


def build_core_tools() -> List[Any]:
    save_tool = StructuredTool.from_function(
        name="save_job_application_package",
        description=(
            "Persist a job-hunt package: filename, company, role title, markdown body "
            "(JD summary, keyword map, cover letter draft)."
        ),
        func=save_job_application_package,
        args_schema=SavePackageInput,
    )
    return [
        Tool(
            name="search_web",
            func=search_web,
            description=(
                "Search the web for job postings, companies, interview info (no API key: DuckDuckGo; "
                "optional SERPER_API_KEY for Google). Use precise queries: role + location + company."
            ),
        ),
        Tool(
            name="wikipedia_lookup",
            func=wikipedia_lookup,
            description="Wikipedia facts about a company, industry, or term (no API key needed).",
        ),
        Tool(
            name="fetch_job_page_text",
            func=fetch_job_page_text,
            description=(
                "Fetch plain text from a job posting or careers page URL. "
                "Use after the user gives a link, or to verify details from a known URL."
            ),
        ),
        save_tool,
        Tool(
            name="list_job_applications",
            func=list_job_applications,
            description="List files saved in the applications folder.",
        ),
        Tool(
            name="read_job_application_file",
            func=read_job_application_file,
            description="Read a saved application file by filename.",
        ),
        Tool(
            name="send_push_notification",
            func=send_push_notification,
            description=(
                "Send a mobile/desktop notification via Pushover. Use when the user wants a ping "
                "(e.g. draft ready, follow-up reminder). Requires PUSHOVER_TOKEN and PUSHOVER_USER."
            ),
        ),
    ]


async def playwright_browser_tools(
    headless: Optional[bool] = None,
) -> Tuple[List[Any], Any, Any]:
    """
    Lab 3: async Playwright toolkit tools (navigate, extract text, etc.).
    Set JOB_HUNT_DISABLE_BROWSER=1 to skip (e.g. CI or machines without Playwright browsers).
    """
    if os.getenv("JOB_HUNT_DISABLE_BROWSER", "").lower() in ("1", "true", "yes"):
        return [], None, None

    if headless is None:
        headless = os.getenv("JOB_HUNT_HEADFUL", "").lower() not in ("1", "true", "yes")

    from playwright.async_api import async_playwright  # noqa: PLC0415

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright
