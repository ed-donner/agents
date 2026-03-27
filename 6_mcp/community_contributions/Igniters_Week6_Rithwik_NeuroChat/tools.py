import asyncio
import xml.etree.ElementTree as ET
from functools import lru_cache

import httpx
from agents import function_tool

_WIKI_HEADERS = {
    "User-Agent": "NeuroChat/1.0 (neuroscience research assistant; contact@example.com)"
}

# _PUBMED_HEADERS = {
#     "User-Agent": "NeuroChat/1.0 (neuroscience research assistant; contact@example.com)"
# }

# _SEMANTIC_SCHOLAR_HEADERS = {
#     "User-Agent": "NeuroChat/1.0 (neuroscience research assistant; contact@example.com)"
# }

@lru_cache(maxsize=256)
def _cached_wiki(query: str) -> str:
    try:
        # Step 1: resolve query → correct article title via opensearch
        search_res = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "opensearch",
                "search": query.strip(),
                "limit": 1,
                "format": "json",
            },
            headers=_WIKI_HEADERS,
            timeout=10,
        )
        search_res.raise_for_status()
        titles = search_res.json()[1]
        if not titles:
            return f"No Wikipedia article found for: {query}"
        article_title = titles[0]

        # Step 2: fetch summary for the resolved title
        formatted = article_title.replace(" ", "_")
        summary_res = httpx.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted}",
            headers=_WIKI_HEADERS,
            timeout=10,
        )
        if summary_res.status_code == 200:
            data = summary_res.json()
            return f"**{data.get('title', article_title)}**\n\n{data.get('extract', 'No information found.')}"
        return f"Wikipedia returned status {summary_res.status_code} for: {article_title}"
    except Exception as e:
        return f"Network error fetching Wikipedia: {e}"


@lru_cache(maxsize=256)
def _cached_pubmed(query: str) -> str:
    """Cached synchronous PubMed fetch."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    try:
        search = httpx.get(
            f"{base}/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmode": "json", "retmax": 3},
            timeout=10,
        )
        search.raise_for_status()
    except Exception as e:
        return f"Error searching PubMed: {e}"

    ids = search.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return "No research papers found on PubMed for that query."

    try:
        fetch = httpx.get(
            f"{base}/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"},
            timeout=15,
        )
        fetch.raise_for_status()
    except Exception as e:
        return f"Error fetching PubMed records: {e}"

    root = ET.fromstring(fetch.text)
    results = []
    for article in root.findall(".//PubmedArticle"):
        try:
            title = article.findtext(".//ArticleTitle", "No title")
            authors = []
            for a in article.findall(".//Author"):
                last = a.findtext("LastName", "")
                first = a.findtext("ForeName", "")
                if last:
                    authors.append(f"{first} {last}".strip())
            author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            journal = article.findtext(".//Journal/Title", "Unknown journal")
            year = article.findtext(".//PubDate/Year", "n.d.")
            pmid = article.findtext(".//PMID", "")
            abstract = article.findtext(".//Abstract/AbstractText", "No abstract available.")
            citation = f"{author_str} ({year}). {title}. {journal}."
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            results.append(
                f"**Title:** {title}\n"
                f"**Authors:** {author_str}\n"
                f"**Journal:** {journal} ({year})\n"
                f"**Citation:** {citation}\n"
                + (f"**Link:** {link}\n" if link else "")
                + f"**Abstract:** {abstract[:600]}{'...' if len(abstract) > 600 else ''}"
            )
        except Exception:
            continue

    return "\n\n---\n\n".join(results) if results else "Could not parse any PubMed articles."


@lru_cache(maxsize=256)
def _cached_semantic_scholar(query: str) -> str:
    """Cached synchronous Semantic Scholar fetch."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": 3,
        "fields": "title,authors,year,abstract,citationCount,openAccessPdf,externalIds",
    }
    try:
        res = httpx.get(url, params=params, timeout=15)
        res.raise_for_status()
    except Exception as e:
        return f"Error fetching Semantic Scholar: {e}"

    papers = res.json().get("data", [])
    if not papers:
        return "No papers found on Semantic Scholar for that query."

    results = []
    for p in papers:
        title = p.get("title", "No title")
        authors = ", ".join(a["name"] for a in p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += " et al."
        year = p.get("year", "n.d.")
        citations = p.get("citationCount", "N/A")
        abstract = (p.get("abstract") or "No abstract available.")[:600]
        pdf = p.get("openAccessPdf") or {}
        pdf_link = pdf.get("url", "")
        doi = (p.get("externalIds") or {}).get("DOI", "")
        doi_link = f"https://doi.org/{doi}" if doi else ""

        results.append(
            f"**Title:** {title}\n"
            f"**Authors:** {authors}\n"
            f"**Year:** {year}  |  **Citations:** {citations}\n"
            + (f"**DOI:** {doi_link}\n" if doi_link else "")
            + (f"**Open Access PDF:** {pdf_link}\n" if pdf_link else "")
            + f"**Abstract:** {abstract}{'...' if len(abstract) >= 600 else ''}"
        )

    return "\n\n---\n\n".join(results)


@function_tool
async def wiki_search(query: str) -> str:
    """
    Search Wikipedia for a neuroscience concept and return a plain-English summary.
    Best for definitions, background knowledge, and simple factual questions.
    """
    # return await asyncio.to_thread(_cached_wiki, query.strip().lower())
    return await asyncio.to_thread(_cached_wiki, query.strip())


@function_tool
async def pubmed_abstracts(query: str) -> str:
    """
    Fetch up to 3 recent PubMed abstracts for a neuroscience research query.
    Returns titles, authors, journal info, truncated abstracts, and citations.
    Best for finding peer-reviewed research with formal citations.
    """
    return await asyncio.to_thread(_cached_pubmed, query.strip().lower())


@function_tool
async def semantic_scholar_search(query: str) -> str:
    """
    Search Semantic Scholar for neuroscience papers.
    Returns citation counts, open-access PDF links, and DOIs alongside abstracts.
    Best for finding highly-cited papers, open-access content, or broader context.
    """
    return await asyncio.to_thread(_cached_semantic_scholar, query.strip().lower())