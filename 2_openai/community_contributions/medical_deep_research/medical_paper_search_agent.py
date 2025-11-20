import requests
from agents import Agent, function_tool, ModelSettings
from typing import Dict, List
import json

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"


@function_tool
def search_medical_papers(query: str, limit: int = 5) -> Dict:
    """
    Search for medical/academic papers using Semantic Scholar API (covers PubMed, arXiv, etc.)
    Returns papers with titles, abstracts, authors, citations, and publication details.
    """
    try:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,authors,year,venue,citationCount,url,externalIds"
        }
        response = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e), "data": []}


INSTRUCTIONS = (
    "You are a medical research assistant specialized in academic literature review. "
    "Given a medical search query, you search academic databases for relevant peer-reviewed papers, "
    "journal articles, and medical research publications.\n\n"
    "For each search:\n"
    "1. Use the search_medical_papers tool to find relevant papers\n"
    "2. Extract key information: title, authors, year, venue/journal, abstract, citation count\n"
    "3. Focus on peer-reviewed sources, clinical studies, and high-impact papers\n"
    "4. Produce a concise summary (2-3 paragraphs, <300 words) that:\n"
    "   - Captures the main findings and methodology\n"
    "   - Notes study type (RCT, meta-analysis, systematic review, etc.)\n"
    "   - Highlights clinical relevance and significance\n"
    "   - Includes key statistics or outcomes when available\n"
    "5. Format as: 'Title (Authors, Year, Journal): [summary]'\n\n"
    "Write succinctly for synthesis into a comprehensive medical report. Focus on evidence and "
    "factual content. No commentary beyond the summary."
)

medical_search_agent = Agent(
    name="MedicalSearchAgent",
    instructions=INSTRUCTIONS,
    tools=[search_medical_papers],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

