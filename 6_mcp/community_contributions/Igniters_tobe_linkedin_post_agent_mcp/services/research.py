from __future__ import annotations

from functools import lru_cache
from typing import Iterable
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from readability import Document

from db.repository import get_repository
from models.entities import SourceItem


class ResearchService:
    def __init__(self) -> None:
        self.repository = get_repository()

    def search_web(self, query: str, max_results: int = 5) -> list[dict]:
        results: list[dict] = []
        with DDGS() as client:
            for item in client.text(query, max_results=max_results):
                results.append(
                    SourceItem(
                        title=item.get("title") or item.get("href") or "Untitled result",
                        url=item.get("href") or "",
                        snippet=item.get("body") or "",
                        source_type="search",
                        score=0.4,
                    ).model_dump()
                )
        return results

    def fetch_page(self, url: str) -> dict:
        with httpx.Client(timeout=12, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "linkedin-post-agent-mcp/0.1"})
            response.raise_for_status()
        return {"url": str(response.url), "html": response.text, "status_code": response.status_code}

    def extract_article(self, url: str, html: str | None = None) -> dict:
        if html is None:
            fetched = self.fetch_page(url)
            html = fetched["html"]
            url = fetched["url"]
        document = Document(html)
        article_html = document.summary()
        title = document.short_title() or url
        soup = BeautifulSoup(article_html, "html.parser")
        text = " ".join(chunk.strip() for chunk in soup.stripped_strings)
        return {
            "title": title,
            "url": url,
            "text": text[:8000],
            "snippet": text[:400],
        }

    def collect_topic_sources(
        self,
        idea_id: str,
        topic: str,
        goal: str,
        notes: str = "",
        urls: list[str] | None = None,
    ) -> dict:
        urls = urls or []
        queries = [
            f"{topic} {goal}",
            f"{topic} best practices recent",
            f"{topic} industry insights",
        ]
        candidates: list[SourceItem] = []
        for url in urls:
            candidates.append(
                SourceItem(
                    title=urlparse(url).netloc or url,
                    url=url,
                    snippet="Provided source",
                    source_type="provided",
                    score=0.9,
                )
            )
        for query in queries:
            try:
                results = self.search_web(query=query, max_results=4)
            except Exception:
                results = []
            for result in results:
                candidates.append(SourceItem.model_validate(result))
        unique_sources: list[SourceItem] = []
        seen_urls: set[str] = set()
        for candidate in candidates:
            if not candidate.url or candidate.url in seen_urls:
                continue
            seen_urls.add(candidate.url)
            unique_sources.append(candidate)
        enriched_sources: list[SourceItem] = []
        for candidate in unique_sources[:4]:
            try:
                article = self.extract_article(candidate.url)
                enriched_sources.append(
                    SourceItem(
                        title=article["title"] or candidate.title,
                        url=article["url"],
                        snippet=article["snippet"] or candidate.snippet,
                        extracted_text=article["text"],
                        source_type=candidate.source_type,
                        score=candidate.score,
                    )
                )
            except Exception:
                enriched_sources.append(candidate)
        summary = self._build_summary(topic=topic, goal=goal, notes=notes, sources=enriched_sources)
        bundle = self.repository.save_research_bundle(
            idea_id=idea_id,
            query=f"{topic} | {goal}",
            summary=summary,
            sources=enriched_sources,
        )
        return bundle.model_dump()

    def _build_summary(self, topic: str, goal: str, notes: str, sources: Iterable[SourceItem]) -> str:
        source_lines = []
        for item in list(sources)[:5]:
            detail = item.snippet or item.extracted_text[:220]
            source_lines.append(f"{item.title}: {detail}")
        details = "\n".join(source_lines)
        return f"Topic: {topic}\nGoal: {goal}\nNotes: {notes}\nSources:\n{details}".strip()


@lru_cache(maxsize=1)
def get_research_service() -> ResearchService:
    return ResearchService()
