from agents import Agent, function_tool
import requests
from typing import Dict
import time

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


@function_tool
def search_pubmed(query: str, max_results: int = 10) -> Dict[str, any]:
    """
    Search PubMed using NCBI E-utilities API and retrieve article summaries.
    
    Args:
        query: Search query (e.g., "NSCLC AND EGFR AND T790M")
        max_results: Maximum number of results to return (default 10)
    
    Returns:
        Dictionary containing search results with titles, abstracts, and PMIDs
    """
    try:
        # Search for articles
        search_url = f"{PUBMED_BASE_URL}esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return {
                "success": True,
                "count": 0,
                "articles": [],
                "message": "No articles found for this query"
            }
        
        # Fetch article details
        time.sleep(0.4)  # Rate limiting: NCBI requests max 3 requests/second
        
        fetch_url = f"{PUBMED_BASE_URL}esummary.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json"
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params, timeout=10)
        fetch_response.raise_for_status()
        fetch_data = fetch_response.json()
        
        articles = []
        result_data = fetch_data.get("result", {})
        
        for pmid in id_list:
            if pmid in result_data:
                article = result_data[pmid]
                articles.append({
                    "pmid": pmid,
                    "title": article.get("title", ""),
                    "authors": [author.get("name", "") for author in article.get("authors", [])[:3]],
                    "journal": article.get("fulljournalname", ""),
                    "pub_date": article.get("pubdate", ""),
                    "doi": article.get("elocationid", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles,
            "query": query
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"PubMed API error: {str(e)}",
            "count": 0,
            "articles": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "count": 0,
            "articles": []
        }


INSTRUCTIONS = """You are a biomedical research specialist tasked with searching PubMed literature.

Given a search term and reason for searching, use the search_pubmed tool to find relevant scientific articles.
After retrieving the results, synthesize a concise summary (2-3 paragraphs, max 300 words) that:
- Highlights key findings from the most relevant articles
- Focuses on clinical relevance (therapies, outcomes, mechanisms)
- Cites specific PMIDs for important findings
- Uses precise scientific language

If the search returns no results or fails, clearly state this and suggest alternative search terms.
"""

pubmed_agent = Agent(
    name="PubMedAgent",
    instructions=INSTRUCTIONS,
    tools=[search_pubmed],
    model="gpt-4o-mini",
)

