"""
Content type router - determines what type of content to create.
"""

from typing import Literal, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState


class ContentTypeDecision(BaseModel):
    """Structured output for content type decision."""
    content_type: str = Field(
        description="Type of content: 'blog' for blog posts, 'social' for social media, 'seo' for SEO-optimized content, 'research' for research only, or 'mixed' for multiple types"
    )
    platform: str = Field(
        description="Platform for social media: 'twitter' for Twitter/X, 'linkedin' for LinkedIn, 'instagram' for Instagram, or 'none' if not social media"
    )
    topic: str = Field(description="The main topic or subject of the content request")
    word_count: int = Field(
        default=1000, 
        description="Desired word count for the content. Default to 1000 if not specified."
    )
    tone: str = Field(
        default="professional",
        description="Tone of the content: 'professional', 'casual', 'friendly', 'formal', 'conversational', etc."
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="List of keywords to include in the content for SEO purposes"
    )
    style: str = Field(
        default="standard",
        description="Content style: 'standard', 'technical', 'creative', 'academic', etc."
    )
    needs_research: bool = Field(
        description="Whether research is needed before content generation. Set to true if the topic requires current information or fact-checking."
    )


def content_type_router(state: ContentState) -> ContentState:
    """Route based on content type detection using structured output."""
    
    # If content type already determined, skip routing
    if state.get("content_type"):
        return state
    
    # Get the user's message
    user_message_content = state["messages"][-1].content if state["messages"] else ""
    if not user_message_content:
        # Default to blog if no message
        return {
            **state,
            "content_type": "blog",
            "platform": "none",
            "topic": "",
            "requirements": {},
        }
    
    # Use LLM with structured output to parse the request
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_structure = llm.with_structured_output(ContentTypeDecision)
    
    system_prompt = """You are an expert content request analyzer. Your job is to understand what type of content the user wants to create and extract all relevant requirements.

Analyze the user's request carefully and extract:
1. Content type: Is it a blog post, social media content, SEO content, research, or mixed?
2. Platform: If social media, which platform (Twitter/X, LinkedIn, Instagram)?
3. Topic: What is the main subject or topic?
4. Requirements: Word count, tone, keywords, style, etc.
5. Research needs: Does this topic need current information or fact-checking?

Be intelligent about extracting requirements even if they're not explicitly stated. For example:
- If user says "blog post", default to 1000-1500 words
- If user says "tweet" or "Twitter", it's social media on Twitter platform
- If user mentions SEO or keywords, it's SEO content
- If topic is about current events or recent developments, research is likely needed"""
    
    user_prompt = f"""Analyze this content creation request:

"{user_message_content}"

Extract all the information about what content to create."""
    
    try:
        # Get structured decision from LLM
        decision = llm_with_structure.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Convert structured output to state format
        requirements = {
            "word_count": decision.word_count,
            "tone": decision.tone,
            "keywords": decision.keywords,
            "style": decision.style,
            "needs_research": decision.needs_research,
        }
        
        return {
            **state,
            "content_type": decision.content_type,
            "platform": decision.platform,
            "topic": decision.topic,
            "requirements": requirements,
        }
        
    except Exception as e:
        # Fallback to simple parsing if structured output fails
        print(f"Warning: Structured output failed, using fallback: {e}")
        
        # Simple fallback
        message_lower = user_message_content.lower()
        content_type = "blog"
        platform = "none"
        
        if any(word in message_lower for word in ["tweet", "twitter", "x.com"]):
            content_type = "social"
            platform = "twitter"
        elif "linkedin" in message_lower:
            content_type = "social"
            platform = "linkedin"
        elif "instagram" in message_lower:
            content_type = "social"
            platform = "instagram"
        elif "seo" in message_lower:
            content_type = "seo"
        elif "research" in message_lower:
            content_type = "research"
        
        # Simple topic extraction
        topic = user_message_content
        if "about" in message_lower:
            topic = user_message_content.split("about")[-1].strip()
        elif "on" in message_lower:
            topic = user_message_content.split("on")[-1].strip()
        
        return {
            **state,
            "content_type": content_type,
            "platform": platform,
            "topic": topic[:200],  # Limit topic length
            "requirements": {"word_count": 1000, "tone": "professional"},
        }

