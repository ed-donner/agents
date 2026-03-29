from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional dependency
    BeautifulSoup = None

try:
    from googlesearch import search as google_search
except ImportError:  # pragma: no cover - optional dependency
    google_search = None

"""
Local Google-backed web search helper.

What this tool does:
- Accepts a plain-text search query.
- Searches Google for that query.
- Opens the top 3 results.
- Scrapes the readable text content from each page.
- Returns a list of dictionaries in this shape:
  {"page_url": "<url>", "content": "<scraped page text>"}

How to call the function directly in Python:
```python
from local_web_search import local_web_search

results = local_web_search("latest AI agent frameworks")
for item in results:
    print(item["page_url"])
    print(item["content"][:500])
```

Notes:
- The tool prefers the `googlesearch` Python package if it is installed.
- If `googlesearch` is unavailable, it falls back to scraping Google result links.
- `beautifulsoup4` is optional but recommended for cleaner HTML parsing.
- Some websites may block scraping or return minimal content; in those cases the
  `content` field will contain an error message for that page.
"""


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10
MAX_RESULTS = 3
MAX_CONTENT_CHARS = 4_000
SKIP_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "google.com",
    "www.google.com",
    "support.google.com",
    "accounts.google.com",
    "policies.google.com",
    "duckduckgo.com",
    "www.duckduckgo.com",
    "html.duckduckgo.com",
}
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self._chunks.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_google_redirect_url(href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.path != "/url":
        return None
    query = parse_qs(parsed.query)
    return query.get("q", [None])[0]


def _extract_duckduckgo_redirect_url(href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.path.startswith("/l/"):
        query = parse_qs(parsed.query)
        return query.get("uddg", [None])[0]
    if parsed.scheme in {"http", "https"}:
        return href
    return None


def _is_supported_result(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    domain = parsed.netloc.lower()
    return not any(domain == blocked or domain.endswith(f".{blocked}") for blocked in SKIP_DOMAINS)


def _search_google_with_library(query: str) -> list[str]:
    if google_search is None:
        return []

    try:
        results = google_search(query, num_results=MAX_RESULTS, advanced=False)
        urls: list[str] = []
        for item in results:
            if isinstance(item, str):
                url = item
            else:
                url = getattr(item, "url", None) or getattr(item, "link", None)
            if isinstance(url, str) and _is_supported_result(url) and url not in urls:
                urls.append(url)
        return [url for url in urls if _is_supported_result(url)][:MAX_RESULTS]
    except Exception:
        return []


def _search_google_with_requests(query: str) -> list[str]:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(
        "https://www.google.com/search",
        params={"q": query, "num": MAX_RESULTS, "hl": "en", "gbv": "1"},
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    if BeautifulSoup is not None:
        soup = BeautifulSoup(response.text, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href], div.yuRUbf a[href]"):
            href = anchor.get("href")
            if not href:
                continue
            url = _extract_google_redirect_url(href)
            if not url and _is_supported_result(href):
                url = href
            if url and _is_supported_result(url) and url not in urls:
                urls.append(url)
            if len(urls) == MAX_RESULTS:
                break
        return urls

    urls = []
    for href in re.findall(r'href="([^"]+)"', response.text):
        url = _extract_google_redirect_url(unescape(href))
        if not url and _is_supported_result(href):
            url = href
        if url and _is_supported_result(url) and url not in urls:
            urls.append(url)
        if len(urls) == MAX_RESULTS:
            break
    return urls


def _search_google(query: str) -> list[str]:
    urls = _search_google_with_library(query)
    if urls:
        return urls
    return _search_google_with_requests(query)


def _search_duckduckgo_with_requests(query: str) -> list[str]:
    headers = {"User-Agent": USER_AGENT, "Referer": "https://duckduckgo.com/"}
    response = requests.post(
        DUCKDUCKGO_HTML_URL,
        data={"q": query},
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    if BeautifulSoup is not None:
        soup = BeautifulSoup(response.text, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a.result__a[href], a[href]"):
            href = anchor.get("href")
            if not href:
                continue
            url = _extract_duckduckgo_redirect_url(href)
            if url and _is_supported_result(url) and url not in urls:
                urls.append(url)
            if len(urls) == MAX_RESULTS:
                break
        return urls

    urls = []
    for href in re.findall(r'href="([^"]+)"', response.text):
        url = _extract_duckduckgo_redirect_url(unescape(href))
        if url and _is_supported_result(url) and url not in urls:
            urls.append(url)
        if len(urls) == MAX_RESULTS:
            break
    return urls


def _search_fallback(query: str) -> list[str]:
    try:
        return _search_duckduckgo_with_requests(query)
    except Exception:
        return []


def _extract_page_text(html: str) -> str:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        return _normalize_whitespace(text)

    parser = _HTMLTextExtractor()
    parser.feed(html)
    return _normalize_whitespace(parser.get_text())


def _fetch_page_content(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    content = _extract_page_text(response.text)
    return content[:MAX_CONTENT_CHARS]


def local_web_search(query: str) -> list[dict[str, Any]]:
    """Search Google, visit the top 3 results, and return scraped page content."""
    results: list[dict[str, Any]] = []

    try:
        urls = _search_google(query)
    except requests.RequestException:
        urls = []
    except Exception:
        urls = []

    if not urls:
        urls = _search_fallback(query)

    if not urls:
        return [
            {
                "page_url": "",
                "content": (
                    "Search failed: Google search and DuckDuckGo fallback both returned no results. "
                    "Google may be blocked by DNS/network restrictions, and the fallback backend did not "
                    "extract any result URLs."
                ),
            }
        ]

    for url in urls[:MAX_RESULTS]:
        try:
            content = _fetch_page_content(url)
        except Exception as exc:
            content = f"Failed to fetch page content: {exc}"

        results.append({"page_url": url, "content": content})

    return results
