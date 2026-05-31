from agents import Agent, function_tool
import requests
from typing import Dict, List


@function_tool
def search_pharmgkb(gene: str, drug: str = None) -> Dict[str, any]:
    """
    Search for pharmacogenomic information about gene-drug interactions.
    This function searches PubMed for PharmGKB-related literature since PharmGKB API requires authentication.
    
    Args:
        gene: Gene symbol (e.g., "EGFR", "KRAS")
        drug: Optional drug name to narrow the search
    
    Returns:
        Dictionary containing pharmacogenomic information
    """
    try:
        # Construct a search query that targets pharmacogenomic literature
        base_query = f"PharmGKB {gene}"
        if drug:
            base_query += f" {drug}"
        base_query += " pharmacogenomics drug response"
        
        # Use PubMed E-utilities to search for PharmGKB literature
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": base_query,
            "retmax": 8,
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
                "message": f"No pharmacogenomic data found for {gene}" + (f" and {drug}" if drug else ""),
                "gene": gene,
                "drug": drug
            }
        
        # Fetch article summaries
        import time
        time.sleep(0.4)  # Rate limiting
        
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
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
                    "authors": [author.get("name", "") for author in article.get("authors", [])[:2]],
                    "journal": article.get("fulljournalname", ""),
                    "pub_date": article.get("pubdate", ""),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
        
        return {
            "success": True,
            "count": len(articles),
            "articles": articles,
            "gene": gene,
            "drug": drug,
            "pharmgkb_url": f"https://www.pharmgkb.org/gene/{gene}",
            "query": base_query
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"PharmGKB search error: {str(e)}",
            "count": 0,
            "articles": [],
            "gene": gene,
            "drug": drug
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "count": 0,
            "articles": [],
            "gene": gene,
            "drug": drug
        }


INSTRUCTIONS = """You are a pharmacogenomics specialist focused on drug-gene interactions and personalized medicine.

Given a gene and optionally a drug name, use the search_pharmgkb tool to find relevant pharmacogenomic information.
After retrieving the results, synthesize a concise summary (2-3 paragraphs, max 300 words) that:
- Describes known drug-gene interactions for the specified gene
- Highlights FDA-approved pharmacogenomic biomarkers when relevant
- Discusses implications for drug dosing, efficacy, or toxicity
- Notes specific mutations and their clinical significance
- Provides evidence level (strong/moderate/weak) when possible

Focus on clinically actionable information. Reference the PharmGKB database and cite PMIDs for key findings.
If limited information is found, clearly state this and suggest related genes or pathways to explore.
"""

pharmgkb_agent = Agent(
    name="PharmGKBAgent",
    instructions=INSTRUCTIONS,
    tools=[search_pharmgkb],
    model="gpt-4o-mini",
)

