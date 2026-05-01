"""
Exposes three neuroscience data tools over the Model Context Protocol (MCP)
using stdio transport. The OpenAI Agents SDK connects to this server as a
subprocess and discovers the tools automatically at runtime.
"""

import asyncio
import xml.etree.ElementTree as ET
from functools import lru_cache

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="neurochat-tools",
    instructions=(
        "Provides three neuroscience data tools: "
        "wiki_search for background knowledge, "
        "pubmed_abstracts for peer-reviewed literature, "
        "semantic_scholar_search for citation data and open-access PDFs."
    ),
)

# Wikipedia requires a User-Agent header — without it the API returns 403.
_WIKI_HEADERS = {
    "User-Agent": "NeuroChat/1.0 (neuroscience research assistant; contact@example.com)"
}


@lru_cache(maxsize=256)
def _fetch_wiki(query: str) -> str:
    """
    Two-step Wikipedia fetch:
    1. opensearch resolves natural language → correct article title
       (fixes case-sensitivity and natural language query mismatches)
    2. /page/summary/ fetches the extract for that exact title
    User-Agent header included on both requests to avoid 403.
    """
    try:
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

        summary_res = httpx.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{article_title.replace(' ', '_')}",
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
def _fetch_pubmed(query: str) -> str:
    """Two-step PubMed fetch: esearch for IDs, then efetch for full records."""
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
def _fetch_semantic_scholar(query: str) -> str:
    """Semantic Scholar Graph API fetch with citation counts and PDF links."""
    try:
        res = httpx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": 3,
                "fields": "title,authors,year,abstract,citationCount,openAccessPdf,externalIds",
            },
            timeout=15,
        )
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
        pdf_link = (p.get("openAccessPdf") or {}).get("url", "")
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



@mcp.tool()
async def wiki_search(query: str) -> str:
    """
    Search Wikipedia for a neuroscience concept and return a plain-English summary.
    Best for definitions, background knowledge, and simple factual questions.
    Examples: 'hippocampus', 'neuroplasticity', 'blood-brain barrier'
    """
    return await asyncio.to_thread(_fetch_wiki, query.strip())


@mcp.tool()
async def pubmed_abstracts(query: str) -> str:
    """
    Fetch up to 3 recent PubMed abstracts for a neuroscience research query.
    Returns titles, authors, journal info, truncated abstracts, and citations.
    Best for finding peer-reviewed research with formal citations.
    Examples: 'BDNF depression', 'adult neurogenesis hippocampus'
    """
    return await asyncio.to_thread(_fetch_pubmed, query.strip())


@mcp.tool()
async def semantic_scholar_search(query: str) -> str:
    """
    Search Semantic Scholar for neuroscience papers.
    Returns citation counts, open-access PDF links, and DOIs alongside abstracts.
    Best for finding highly-cited papers, open-access content, or broader context.
    Examples: 'synaptic plasticity LTP', 'Alzheimer amyloid beta'
    """
    return await asyncio.to_thread(_fetch_semantic_scholar, query.strip())



if __name__ == "__main__":
    mcp.run(transport="stdio")