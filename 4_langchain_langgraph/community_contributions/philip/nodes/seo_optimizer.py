"""
SEO optimizer node.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


def seo_optimizer_node(state: ContentState) -> ContentState:
    """Optimize content for SEO."""
    
    # Skip if not SEO content type
    if state.get("content_type") != "seo":
        return state
    
    # Skip if already optimized
    if state.get("seo_metadata") and state.get("final_content"):
        return state
    
    topic = state.get("topic", "")
    requirements = state.get("requirements", {}) or {}  # Handle None case
    draft_content = state.get("draft_content", "")
    
    # If no draft content, generate it first
    if not draft_content:
        # Generate SEO-optimized content
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        system_prompt = """You are an SEO content expert. Create SEO-optimized articles that:
- Include target keywords naturally
- Have proper heading structure (H1, H2, H3)
- Are well-structured and readable
- Include meta tags
- Follow SEO best practices"""
        
        word_count = requirements.get("word_count", 1500) if requirements else 1500
        keywords = requirements.get("keywords", []) if requirements else []
        
        user_prompt = f"""Create an SEO-optimized article about: {topic}

Requirements:
- Word count: {word_count} words
- Keywords: {', '.join(keywords) if keywords else 'none specified'}
- Format: Markdown with proper headings
- Include: Title, meta description, and optimized content

Generate the complete SEO-optimized article."""
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        draft_content = response.content
    
    # Generate SEO metadata
    seo_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    keywords = requirements.get("keywords", []) if requirements else []
    keyword_str = ", ".join(keywords) if keywords else "none specified"
    
    seo_prompt = f"""Generate SEO metadata for this article about "{topic}":

Keywords: {keyword_str}

Article preview:
{draft_content[:500]}...

Generate:
1. SEO-optimized title (50-60 characters, include primary keyword)
2. Meta description (150-160 characters, include keywords, compelling)
3. Primary and secondary keywords
4. SEO score and recommendations"""
    
    seo_response = seo_llm.invoke([
        SystemMessage(content="You are an SEO expert. Generate comprehensive SEO metadata."),
        HumanMessage(content=seo_prompt)
    ]).content
    
    # Parse SEO metadata
    seo_metadata = {
        "title": topic,  # Can be improved with parsing
        "meta_description": seo_response[:160] if len(seo_response) > 160 else seo_response,
        "keywords": keywords,
        "seo_analysis": seo_response,
    }
    
    return {
        **state,
        "draft_content": draft_content,
        "final_content": draft_content,
        "seo_metadata": seo_metadata,
    }

