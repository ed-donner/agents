"""
Research node - gathers information about the topic.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def research_node(state: ContentState) -> ContentState:
    """Research the topic and gather information."""
    
    # Skip if research already done
    if state.get("research_data"):
        return state
    
    # Skip if research not needed
    if not state.get("requirements", {}).get("needs_research", True):
        return state
    
    topic = state.get("topic", "")
    if not topic:
        return state
    
    # Use web search
    serper = GoogleSerperAPIWrapper(serper_api_key=os.getenv("SERPER_API_KEY"))
    
    try:
        # Search for the topic
        search_results = serper.run(topic)
        
        # Summarize research findings
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        system_prompt = """You are a research assistant. Summarize the search results into key points and information relevant to the topic."""
        
        user_prompt = f"""Topic: {topic}

Search Results:
{search_results}

Summarize the key information, facts, and insights from these search results. Focus on information that would be useful for creating content about this topic."""
        
        summary = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]).content
        
        research_data = {
            "topic": topic,
            "search_results": search_results,
            "summary": summary,
            "sources": []  
        }
        
        return {
            **state,
            "research_data": research_data,
        }
    except Exception as e:
        # If search fails, continue without research
        return {
            **state,
            "research_data": {
                "topic": topic,
                "summary": f"Research unavailable: {str(e)}",
                "sources": []
            }
        }

