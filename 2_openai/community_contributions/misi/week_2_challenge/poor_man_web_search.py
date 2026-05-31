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


"""
Local DuckDuckGo-backed web search helper.

What this tool does:
- Accepts a plain-text search query.
- Searches DuckDuckGo for that query.
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
- `beautifulsoup4` is optional but recommended for cleaner HTML parsing.
- Some websites may block scraping or return minimal content; in those cases the
    `content` field will contain an error message for that page.
"""


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10
MAX_RESULTS = 10
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
    return not any(
        domain == blocked or domain.endswith(f".{blocked}") for blocked in SKIP_DOMAINS
    )


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


# Public API
def local_web_search(query: str) -> list[dict[str, Any]]:
    """
    Search DuckDuckGo, visit up to the top 10 results, and return scraped page content for the first 3 available pages.
    If a page returns an error (403, 404, etc.), try the next result until 3 valid contents are found or all are exhausted.
    """
    try:
        urls = _search_duckduckgo_with_requests(query)
    except requests.RequestException:
        urls = []
    except Exception:
        urls = []

    if not urls:
        return [
            {
                "page_url": "",
                "content": (
                    "Search failed: DuckDuckGo search returned no results. "
                    "DuckDuckGo may be blocked by DNS/network restrictions, or no result URLs were extracted."
                ),
            }
        ]

    results: list[dict[str, Any]] = []
    attempted = 0
    for url in urls:
        if len(results) == 3:
            break
        try:
            content = _fetch_page_content(url)
            # If the content is too short or looks like an error, skip
            if not content or content.lower().startswith("failed to fetch"):
                continue
            results.append({"page_url": url, "content": content})
        except Exception as exc:
            continue
        attempted += 1

    # If less than 3 valid results, fill with error messages
    while len(results) < 3:
        results.append({"page_url": "", "content": "No more valid results found."})
    return results
