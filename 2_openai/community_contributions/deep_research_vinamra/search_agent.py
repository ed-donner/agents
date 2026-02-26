import os
import requests
from typing import Dict, List
from agents import Agent, function_tool, ModelSettings
from guardrails import validate_research_input
from model_config import mimo_model


@function_tool
def serper_search(query: str) -> str:
    """
    Perform web search using Serper API and return formatted results
    
    Args:
        query: Search query string
        
    Returns:
        Formatted string with search results
    """
    api_key = os.getenv("SERPER_API_KEY")
    
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": 10
    }
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format results for the agent
        formatted_results = f"Search results for: {query}\n\n"
        
        if "organic" in data:
            for i, item in enumerate(data["organic"][:5], 1):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                formatted_results += f"{i}. **{title}**\n"
                formatted_results += f"   {snippet}\n"
                formatted_results += f"   Source: {link}\n\n"
        
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            formatted_results += f"\n**Key Information:**\n"
            if "description" in kg:
                formatted_results += f"{kg['description']}\n"
        
        return formatted_results if formatted_results else "No results found"
        
    except Exception as e:
        return f"Search failed: {str(e)}"


INSTRUCTIONS = """You are a skilled research analyst specializing in information extraction and synthesis.

**Task**: Given a search term, use the serper_search tool to search the web and produce a concise, high-quality summary.

**Process:**
1. Use the serper_search tool with the search query
2. Analyze the returned results (titles, snippets, links)
3. Synthesize a concise summary from the information

**Requirements:**
- Length: 2-3 paragraphs, under 300 words
- Focus: Capture key facts, data, and insights
- Style: Succinct and information-dense (no fluff)
- Quality: Prioritize credible sources and recent information
- Format: No introductions or conclusions - just the core information

**What to include:**
- Key facts, statistics, and data points
- Main findings or conclusions
- Important context or background
- Notable examples or case studies
- Expert opinions or authoritative statements

**What to avoid:**
- Vague generalizations
- Redundant information  
- Marketing language or promotional content
- Personal opinions (yours)
- Unnecessary context or filler

**Output format:**
Provide ONLY the summary itself. No preambles like "Here's a summary" or "Based on the search".
This summary will be used by another agent to synthesize a comprehensive report."""

search_agent = Agent(
    name="SearchAgent",
    instructions=INSTRUCTIONS,
    tools=[serper_search],
    model=mimo_model,
)