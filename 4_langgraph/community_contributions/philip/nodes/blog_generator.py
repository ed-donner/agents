"""
Blog post generator node.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


def blog_generator_node(state: ContentState) -> ContentState:
    """Generate a blog post."""
    
    if state.get("content_type") != "blog":
        return state
    
    # Skip if already generated
    if state.get("final_content"):
        return state
    
    topic = state.get("topic", "")
    requirements = state.get("requirements", {}) or {}
    research_data = state.get("research_data") or {}  # Handle None case
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Build system prompt
    system_prompt = """You are an expert blog post writer. Create high-quality, engaging blog posts with:
- Clear structure (introduction, body sections, conclusion)
- SEO-friendly headings (H1, H2, H3)
- Engaging content
- Proper formatting
- Call-to-action at the end

CRITICAL: You MUST generate the COMPLETE blog post. Do not stop mid-sentence or leave sections incomplete. The entire post must be finished.

Format the output in Markdown."""
    
    # Build user prompt
    word_count = requirements.get("word_count", 1000)
    tone = requirements.get("tone", "professional")
    keywords = requirements.get("keywords", []) or []
    
    research_info = ""
    if research_data and research_data.get("summary"):
        research_info = f"\n\nResearch Summary:\n{research_data['summary']}\n\nUse this research to add depth, facts, and authority to your blog post."
    
    keyword_info = ""
    if keywords:
        keyword_info = f"\n\nKeywords to include naturally: {', '.join(keywords)}"
    
    user_prompt = f"""Write a COMPLETE {word_count}-word blog post about: {topic}

CRITICAL REQUIREMENTS:
- Word count: You MUST write approximately {word_count} words. This is not optional.
- Tone: {tone}
- Format: Markdown with proper headings (H1 for title, H2 for main sections, H3 for subsections)
- Structure: 
  * Introduction (100-150 words)
  * 4-6 body sections (each 200-300 words)
  * Conclusion (100-150 words)
  * Call-to-action (50-100 words)
- COMPLETENESS: The entire blog post must be complete. Every section must be fully written. Do not stop mid-sentence.
{keyword_info}
{research_info}

Generate the COMPLETE blog post in Markdown format. Ensure it meets the word count requirement."""
    
    # Generate content
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    content = response.content
    
    # Generate SEO metadata
    seo_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    seo_prompt = f"""Based on this blog post about "{topic}", generate:
1. SEO-optimized title (50-60 characters)
2. Meta description (150-160 characters)
3. Primary keywords

Blog post:
{content[:500]}..."""
    
    seo_response = seo_llm.invoke([
        SystemMessage(content="You are an SEO expert. Generate SEO metadata."),
        HumanMessage(content=seo_prompt)
    ]).content
    
    # Parse SEO metadata
    seo_metadata = {
        "title": topic,  # Default
        "meta_description": seo_response[:160] if len(seo_response) > 160 else seo_response,
        "keywords": keywords,
    }
    
    return {
        **state,
        "draft_content": content,
        "final_content": content,
        "seo_metadata": seo_metadata,
    }

