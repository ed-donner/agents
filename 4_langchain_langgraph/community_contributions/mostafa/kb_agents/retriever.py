import os
from datetime import datetime
from tqdm import tqdm
from kb_state import KBState
from utils import get_content_from_url
from models import ResearchPlan, RetrievedSource 
from langchain_community.utilities import GoogleSerperAPIWrapper


SERPER_API_KEY = os.getenv("SERPER_API_KEY")
serper = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY)

def search_retrieve(state: KBState) -> dict:
    """Executes searches via Serper and retrieves page content."""
    sources: list[RetrievedSource] = []

    if not state["research_plan"]:
        return {
            'messages': state['messages'] + [{
                'role': 'system',
                'content': 'No research plan found. Skipping search retrieval.'
            }]
        }

    plan: ResearchPlan = state["research_plan"]

    total_queries = sum(len(sub.search_queries) for sub in plan.subtopics)

    with tqdm(total=total_queries, desc="Executing search queries", unit='query') as pbar:
        for subtopic in plan.subtopics:
            for query in subtopic.search_queries:
                results = serper.results(query).get('organic', [])

                for result in results[:5]:  # limit to top 5 results per query
                    url = result.get('link', '')
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    content = get_content_from_url(url)
                    sources.append(RetrievedSource(
                        subtopic=subtopic.name,
                        query=query,
                        url=url,
                        title=title,
                        snippet=snippet,
                        content=content,
                        retrieved_at=datetime.now().isoformat()
                    ))

                pbar.set_postfix(sources=len(sources),
                                 subtopic=subtopic.name[:20])
                pbar.update(1)

    return {
        'raw_sources': sources,
        'messages': [{
            'role': 'retriever',
            'content': f'Retrieved {len(sources)} sources for {len(state['research_plan'].subtopics)} subtopics.'
        }]
    }


