"""
Search Executor - executes queries and collects raw results.

This is NOT an agent that synthesizes. It:
- Executes search queries using WebSearchTool
- Collects raw snippets and URLs
- Tags each result with an inferred SourceTier
- Deduplicates by URL
- Returns structured data for the Synthesizer

No interpretation happens here - just collection and classification.
"""

import asyncio
from urllib.parse import urlparse

from agents import Agent, WebSearchTool, ModelSettings, Runner
from models import SearchPlan, SearchQuery, SearchResult, SourceTier, PublisherType


class SearchResults:
    """
    Aggregated, deduplicated search results.
    
    Simple container - not a Pydantic model to avoid JSON schema issues.
    """
    def __init__(self):
        self.results: list[SearchResult] = []
        self._urls_seen: set[str] = set()
    
    def add_result(self, result: SearchResult) -> bool:
        """Add a result if not duplicate. Returns True if added."""
        if result.url not in self._urls_seen:
            self.results.append(result)
            self._urls_seen.add(result.url)
            return True
        return False


# Domain patterns for source tier inference
PRIMARY_DOMAINS = {
    ".gov", ".edu", "arxiv.org", "nature.com", "science.org", 
    "sec.gov", "who.int", "nih.gov", "cdc.gov", "europa.eu",
    "pubmed", "scholar.google", "jstor.org", "ieee.org"
}

SECONDARY_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "nytimes.com", "wsj.com",
    "economist.com", "ft.com", "bloomberg.com", "theguardian.com",
    "techcrunch.com", "arstechnica.com", "wired.com"
}

EXCLUDED_DOMAINS = {
    "twitter.com", "x.com", "facebook.com", "instagram.com", 
    "tiktok.com", "reddit.com", "threads.net"
}


def extract_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def infer_publisher_type(url: str) -> PublisherType:
    """Infer the publisher type from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
    except Exception:
        return PublisherType.UNKNOWN
    
    # Government
    if any(x in domain for x in [".gov", ".gov.", "europa.eu"]):
        return PublisherType.GOVERNMENT
    
    # Academic
    if any(x in domain for x in [".edu", "arxiv.org", "scholar.google", "jstor.org", 
                                   "ieee.org", "pubmed", "nature.com", "science.org"]):
        return PublisherType.ACADEMIC
    
    # Social media
    for excluded in EXCLUDED_DOMAINS:
        if excluded in domain:
            return PublisherType.SOCIAL
    
    # News outlets
    for secondary in SECONDARY_DOMAINS:
        if secondary in domain:
            return PublisherType.NEWS
    
    # Blogs
    if any(x in domain for x in ["blog.", "medium.com", "substack.com", "dev.to"]):
        return PublisherType.BLOG
    
    # Default to vendor (company sites, etc.)
    return PublisherType.VENDOR


def infer_source_tier(url: str) -> SourceTier:
    """Infer the source quality tier from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
    except Exception:
        return SourceTier.OPINION  # Default to low trust on parse failure
    
    # Check exclusions first
    for excluded in EXCLUDED_DOMAINS:
        if excluded in domain:
            return SourceTier.EXCLUDED
    
    # Check primary sources
    for primary in PRIMARY_DOMAINS:
        if primary in domain or domain.endswith(primary):
            return SourceTier.PRIMARY
    
    # Check for PDF/academic indicators in path
    if ".pdf" in path or "paper" in path or "research" in path:
        return SourceTier.PRIMARY
    
    # Check secondary sources
    for secondary in SECONDARY_DOMAINS:
        if secondary in domain:
            return SourceTier.SECONDARY
    
    # Check for vendor patterns
    if any(x in domain for x in ["blog.", "medium.com", "substack.com"]):
        return SourceTier.OPINION
    
    # Default to vendor (company sites, etc.)
    return SourceTier.VENDOR


# Agent that performs a single search and returns raw results
SEARCH_INSTRUCTIONS = """You are a research assistant performing web searches.

Your job is to:
1. Execute the provided search query using your web search tool
2. Return the raw results as a structured list

For each result, extract:
- The URL
- The page title
- A relevant snippet (the most informative excerpt, 2-3 sentences max)

Do NOT summarize or synthesize. Just collect and structure the raw data.
Return up to 5 results per search, prioritizing diversity of sources.
"""

search_agent = Agent(
    name="SearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="medium")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)


async def execute_single_search(query: SearchQuery) -> list[SearchResult]:
    """Execute a single search and return structured results."""
    input_text = f"Search query: {query.query}\nReason: {query.reason}"
    
    try:
        result = await Runner.run(search_agent, input_text)
        output = str(result.final_output)
        
        # Parse the output into SearchResult objects
        # The agent returns text, so we need to extract URLs and snippets
        # For now, create a single result from the summary
        # In production, you'd want structured output from the agent
        
        return [SearchResult(
            query=query.query,
            url=f"search://{query.query.replace(' ', '_')}",  # Placeholder
            title=query.query,
            snippet=output[:500] if len(output) > 500 else output,
            inferred_tier=SourceTier.SECONDARY,  # Will be refined
        )]
    except Exception as e:
        print(f"Search failed for '{query.query}': {e}")
        return []


async def execute_search_plan(plan: SearchPlan) -> SearchResults:
    """Execute all searches in the plan and return deduplicated results."""
    results = SearchResults()
    
    # Run searches concurrently
    tasks = [execute_single_search(query) for query in plan.searches]
    all_results = await asyncio.gather(*tasks)
    
    # Flatten and deduplicate
    for search_results in all_results:
        for result in search_results:
            # Enrich with domain, publisher type, and tier
            result.domain = extract_domain(result.url)
            result.publisher_type = infer_publisher_type(result.url)
            result.inferred_tier = infer_source_tier(result.url)
            
            # Skip excluded sources
            if result.inferred_tier != SourceTier.EXCLUDED:
                results.add_result(result)
    
    print(f"Collected {len(results.results)} unique results")
    return results
