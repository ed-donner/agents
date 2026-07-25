import asyncio
import json
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from agents import function_tool
from bs4 import BeautifulSoup

DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _resolve_result_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        url = f"https:{url}"

    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        redirected = parse_qs(parsed.query).get("uddg", [])
        if redirected:
            return unquote(redirected[0])
    return url


def _extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(
        ["script", "style", "noscript", "svg", "header", "footer", "nav", "form", "aside"]
    ):
        tag.decompose()

    container = soup.find("main") or soup.find("article") or soup.body or soup
    return _compact(container.get_text(" ", strip=True))[:1800]


def _parse_html_results(html: str, max_results: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for block in soup.select(".result"):
        anchor = block.select_one("a.result__a")
        if not anchor:
            continue

        url = _resolve_result_url(anchor.get("href", ""))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        snippet_node = block.select_one(".result__snippet")
        results.append(
            {
                "title": _compact(anchor.get_text(" ", strip=True)),
                "url": url,
                "snippet": _compact(snippet_node.get_text(" ", strip=True))
                if snippet_node
                else "",
                "excerpt": "",
            }
        )
        if len(results) >= max_results:
            break

    return results


def _parse_lite_results(html: str, max_results: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for anchor in soup.select("a"):
        title = _compact(anchor.get_text(" ", strip=True))
        url = _resolve_result_url(anchor.get("href", ""))
        if not title or not url or url in seen_urls:
            continue
        if "duckduckgo.com" in urlparse(url).netloc:
            continue
        seen_urls.add(url)
        results.append(
            {
                "title": title,
                "url": url,
                "snippet": "",
                "excerpt": "",
            }
        )
        if len(results) >= max_results:
            break

    return results


async def _fetch_page_excerpt(client: httpx.AsyncClient, url: str) -> str:
    try:
        response = await client.get(url, headers=DEFAULT_HEADERS, timeout=15.0)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return ""
        return _extract_page_text(response.text)
    except Exception:
        return ""


async def _search_web(query: str, max_results: int, pages_to_fetch: int) -> dict:
    max_results = min(max(1, max_results), 8)
    pages_to_fetch = min(max(1, pages_to_fetch), 3)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(
            DUCKDUCKGO_HTML_URL,
            params={"q": query},
            headers=DEFAULT_HEADERS,
            timeout=20.0,
        )
        response.raise_for_status()

        results = _parse_html_results(response.text, max_results=max_results)
        if not results:
            results = _parse_lite_results(response.text, max_results=max_results)

        excerpt_tasks = [
            asyncio.create_task(_fetch_page_excerpt(client, result["url"]))
            for result in results[:pages_to_fetch]
        ]
        excerpts = await asyncio.gather(*excerpt_tasks, return_exceptions=True)
        for result, excerpt in zip(results[:pages_to_fetch], excerpts):
            if isinstance(excerpt, str):
                result["excerpt"] = excerpt

        return {"query": query, "results": results}


@function_tool(
    description_override="Search the public web and return result titles, snippets, URLs, and extracted page text.",
    use_docstring_info=False,
)
async def search_web(query: str, max_results: int = 5, pages_to_fetch: int = 3) -> str:
    payload = await _search_web(
        query=query,
        max_results=max_results,
        pages_to_fetch=pages_to_fetch,
    )
    return json.dumps(payload, ensure_ascii=False, indent=2)
