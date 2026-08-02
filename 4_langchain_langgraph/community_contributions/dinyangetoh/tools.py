"""
tools.py — External API wrapper functions for Academic Deep Researcher.

Each function is stateless, handles its own errors gracefully, and returns
a consistent list-of-dicts format that matches the raw_results State field.

Result dict shape:
    {
        "source":        str,   # "semantic_scholar" | "arxiv" | "core" | "tavily" | "pubmed"
        "source_type":   str,   # "paper" | "preprint" | "web" | "news"
        "title":         str,
        "content":       str,   # abstract or extracted text, truncated to 1500 chars
        "url":           str,
        "year":          int | None,
        "citation_count": int | None,
    }
"""

import os
import random
import time
import requests
import arxiv
from typing import List, Optional


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_FIELDS = (
    "title,abstract,year,citationCount,openAccessPdf,externalIds,authors"
)


def _s2_headers() -> dict:
    h = {}
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if key:
        h["x-api-key"] = key
    return h


def search_semantic_scholar(query: str, limit: int = 8) -> List[dict]:
    """Search Semantic Scholar for academic papers with citation metadata.

    Optional: without SEMANTIC_SCHOLAR_API_KEY, calls are skipped (returns []).
    Set SEMANTIC_SCHOLAR_ALLOW_ANONYMOUS=true to use the public rate-limited API anyway.
    With a key: retries on HTTP 429; includes title-only rows when abstract is missing.
    """
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    allow_anon = os.getenv("SEMANTIC_SCHOLAR_ALLOW_ANONYMOUS",
                           "").lower() in ("1", "true", "yes")
    if not key and not allow_anon:
        print(
            "[Semantic Scholar] Skipped (optional) — no SEMANTIC_SCHOLAR_API_KEY. "
            "Add a key to enable, or set SEMANTIC_SCHOLAR_ALLOW_ANONYMOUS=true for the public API."
        )
        return []

    params = {"query": query[:2000], "limit": limit,
              "fields": SEMANTIC_SCHOLAR_FIELDS}
    last_err: Optional[Exception] = None

    for attempt in range(5):
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_URL,
                params=params,
                headers=_s2_headers(),
                timeout=20,
            )
            if response.status_code == 429:
                wait = min(2.0 ** attempt + random.uniform(0.5, 2.0), 60.0)
                print(
                    f"[Semantic Scholar] 429 — backing off {wait:.1f}s (attempt {attempt + 1}/5)")
                time.sleep(wait)
                continue
            response.raise_for_status()
            papers = response.json().get("data", [])

            results = []
            for p in papers:
                abstract = (p.get("abstract") or "").strip()
                title = (p.get("title") or "").strip()
                if abstract:
                    content = abstract[:1500]
                elif title:
                    content = f"(No abstract) {title}"[:1500]
                else:
                    continue
                pdf_info = p.get("openAccessPdf") or {}
                ext_ids = p.get("externalIds") or {}
                results.append({
                    "source": "semantic_scholar",
                    "source_type": "paper",
                    "title": title,
                    "content": content,
                    "url": pdf_info.get("url", ""),
                    "year": p.get("year"),
                    "citation_count": p.get("citationCount", 0),
                    "arxiv_id": ext_ids.get("ArXiv"),
                })

            time.sleep(0.35)
            return results

        except Exception as e:
            last_err = e
            if "429" in str(e).lower():
                wait = min(2.0 ** attempt + random.uniform(0.5, 2.0), 60.0)
                time.sleep(wait)
                continue
            print(f"[Semantic Scholar] Error: {e}")
            return []

    print(f"[Semantic Scholar] Error after retries: {last_err}")
    return []


def search_arxiv(query: str, max_results: int = 5) -> List[dict]:
    """Search ArXiv for preprints and return full abstracts with PDF links.

    Uses arxiv.Client with >=3s between requests (API terms) and retries on failures.
    """
    try:
        search = arxiv.Search(
            query=query[:2000],
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        client = arxiv.Client(
            page_size=min(100, max_results + 2),
            delay_seconds=3.5,
            num_retries=5,
        )
        results = []
        for paper in client.results(search):
            results.append({
                "source": "arxiv",
                "source_type": "preprint",
                "title": paper.title,
                "content": paper.summary[:1500],
                "url": paper.pdf_url,
                "year": paper.published.year if paper.published else None,
                "citation_count": None,
            })
        return results

    except Exception as e:
        print(f"[ArXiv] Error: {e}")
        return []


CORE_API_URL = "https://api.core.ac.uk/v3/search/works"


def search_core(query: str, limit: int = 5) -> List[dict]:
    api_key = os.getenv("CORE_API_KEY", "")
    if not api_key:
        print("[CORE] CORE_API_KEY not set — skipping CORE search.")
        return []

    try:
        last_exc: Optional[Exception] = None
        data = None
        for attempt in range(4):
            try:
                response = requests.get(
                    CORE_API_URL,
                    params={"q": query[:1500], "limit": limit},
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=20,
                )
                if response.status_code in (429, 500, 502, 503, 504):
                    wait = min(1.5 ** attempt + random.uniform(0.2, 1.0), 30.0)
                    print(
                        f"[CORE] HTTP {response.status_code} — retry in {wait:.1f}s")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                last_exc = e
                wait = min(1.5 ** attempt + random.uniform(0.2, 1.0), 30.0)
                time.sleep(wait)
        if data is None:
            raise last_exc or RuntimeError("CORE request failed")

        results = []
        for work in data.get("results", []):
            abstract = (work.get("abstract") or "").strip()
            if not abstract:
                continue
            url = work.get("downloadUrl") or ""
            if not url:
                source_urls = work.get("sourceFulltextUrls") or []
                url = source_urls[0] if source_urls else ""
            results.append({
                "source": "core",
                "source_type": "paper",
                "title": work.get("title", ""),
                "content": abstract[:1500],
                "url": url,
                "year": work.get("yearPublished"),
                "citation_count": None,
            })
        return results

    except Exception as e:
        print(f"[CORE] Error: {e}")
        return []


def search_tavily(query: str, max_results: int = 5) -> List[dict]:
    try:
        try:
            from langchain_tavily import TavilySearch
            tool = TavilySearch(max_results=max_results)
        except ImportError:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tool = TavilySearchResults(max_results=max_results)
        raw = tool.invoke({"query": query})
        if isinstance(raw, dict) and "results" in raw:
            raw = raw["results"]
        if not isinstance(raw, list):
            raw = []
        results = []
        for item in raw:
            results.append({
                "source": "tavily",
                "source_type": "web",
                "title": item.get("title", ""),
                "content": (item.get("content") or "")[:1500],
                "url": item.get("url", ""),
                "year": None,
                "citation_count": None,
            })
        return results
    except Exception as e:
        print(f"[Tavily] Error: {e}")
        return []


def search_pubmed(query: str, top_k: int = 5) -> List[dict]:
    try:
        from langchain_community.utilities import PubMedAPIWrapper
        pubmed = PubMedAPIWrapper(top_k_results=top_k)
        docs = pubmed.load(query)
        results = []
        for doc in docs:
            meta = doc.metadata or {}
            uid = meta.get("uid", "")
            results.append({
                "source": "pubmed",
                "source_type": "paper",
                "title": meta.get("title", ""),
                "content": doc.page_content[:1500],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}" if uid else "",
                "year": None,
                "citation_count": None,
            })
        return results
    except Exception as e:
        print(f"[PubMed] Error: {e}")
        return []


def send_email_report(report_md: str, recipient: str, topic: str) -> bool:
    import html as html_lib
    import markdown as md_lib
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    api_key = os.getenv("SENDGRID_API_KEY", "")
    sender = os.getenv("EMAIL_FROM", "")
    if not api_key or not sender:
        print("[Email] SENDGRID_API_KEY or EMAIL_FROM not configured — skipping.")
        return False
    if not recipient:
        print("[Email] No recipient address provided — skipping.")
        return False
    try:
        inner = md_lib.markdown(report_md, extensions=["extra", "nl2br"])
        safe_topic = html_lib.escape(topic)
        html_body = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\" />"
            "<style>body{font-family:system-ui,Segoe UI,sans-serif;line-height:1.5;"
            "max-width:720px;margin:1rem auto;padding:0 1rem;} pre{white-space:pre-wrap;}"
            "</style></head><body>"
            f"<h1>Research report: {safe_topic}</h1>"
            f"<div class=\"content\">{inner}</div>"
            "</body></html>"
        )
        message = Mail(
            from_email=sender,
            to_emails=recipient.strip(),
            subject=f"Research Report: {topic[:200]}",
            html_content=html_body,
        )
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        print(f"[Email] Report sent to {recipient}")
        return True
    except Exception as e:
        print(f"[Email] Error: {e}")
        return False
