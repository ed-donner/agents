"""Serper search tools, CV parsers, and custom website scraper browser tools."""

from __future__ import annotations
import asyncio
from pathlib import Path
from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from autogen_ext.tools.langchain import LangChainToolAdapter
from autogen_core.tools import FunctionTool

from dotenv import load_dotenv
load_dotenv(override=True)

from website_scraper import fetch_js_website


_web_serper = GoogleSerperAPIWrapper(type="search")
_news_serper = GoogleSerperAPIWrapper(type="news")

@tool
def web_search(query: str) -> str:
    """Search the web for general information about a company, job role, or technology."""
    return _web_serper.run(query)

@tool
def news_search(query: str) -> str:
    """Search recent news about a company (funding, layoffs, product launches, strategy)."""
    return _news_serper.run(query)

web_search_tool = LangChainToolAdapter(web_search)
news_search_tool = LangChainToolAdapter(news_search)


def scrape_job_posting(url: str) -> str:
    """Scrape the job description and application questions from a job posting URL.

    Fetches the base URL, URL/apply, and URL/application — whichever pages exist —
    and returns their combined visible text.
    """
    base = url.rstrip("/")
    sections = []
    for target in (base, f"{base}/apply", f"{base}/application"):
        try:
            text = fetch_js_website(target)
            if text.strip():
                sections.append(f"=== {target} ===\n{text}")
        except Exception:
            pass
    return "\n\n".join(sections) if sections else "No content scraped."


async def get_browser_tools() -> list:
    """Return autogen FunctionTool instances backed by the custom website scraper."""
    return [
        FunctionTool(scrape_job_posting, name="scrape_job_posting",
                     description=(
                         "Scrape a job posting URL. Fetches the base URL, URL/apply, and "
                         "URL/application to capture the full job description and application questions."
                     ), strict=True),
    ]


def _parse_pdf(path: Path) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    if not pages:
        raise ValueError(f"No text extracted from {path}")
    return "\n\n".join(pages)

def load_cv(paths: list[str | Path]) -> tuple[str, str]:
    """Return (cv_text, cv_typst) from a list of PDF / TXT / Typst paths."""
    cv_text, cv_typst = "", ""
    for p in [Path(x) for x in paths]:
        if not p.exists():
            continue
        if p.suffix == ".pdf" and not cv_text:
            cv_text = _parse_pdf(p)
        elif p.suffix == ".typ":
            cv_typst = p.read_text(encoding="utf-8")
        elif p.suffix == ".txt" and not cv_text:
            cv_text = p.read_text(encoding="utf-8")
    if not cv_text and cv_typst:
        cv_text = cv_typst
    if not cv_typst and cv_text:
        cv_typst = cv_text
    if not cv_text:
        raise ValueError("No valid CV content found in provided files")
    return cv_text, cv_typst
