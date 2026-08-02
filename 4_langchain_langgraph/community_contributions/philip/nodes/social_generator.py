"""
Social media content generator node.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


def social_generator_node(state: ContentState) -> ContentState:
    """Generate social media content."""
    
    # Skip if not social content type
    if state.get("content_type") != "social":
        return state
    
    # Skip if already generated
    if state.get("final_content"):
        return state
    
    topic = state.get("topic", "")
    platform = state.get("platform", "linkedin")
    requirements = state.get("requirements", {}) or {}
    research_data = state.get("research_data") or {}  # Handle None case
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Platform-specific prompts
    platform_configs = {
        "twitter": {
            "max_chars": 280,
            "description": "Twitter/X post",
            "hashtags": True,
            "thread": False,
        },
        "linkedin": {
            "max_chars": 3000,
            "description": "LinkedIn professional post",
            "hashtags": True,
            "thread": False,
        },
        "instagram": {
            "max_chars": 2200,
            "description": "Instagram caption",
            "hashtags": True,
            "thread": False,
        }
    }
    
    config = platform_configs.get(platform, platform_configs["linkedin"])
    
    system_prompt = f"""You are an expert social media content creator. Create engaging {config['description']}s that:
- Are engaging and authentic
- Include relevant hashtags
- Have a clear message
- Encourage engagement
- Stay within character limits

Platform: {platform.upper()}
Max characters: {config['max_chars']}"""
    
    word_count = requirements.get("word_count", 200)
    tone = requirements.get("tone", "professional" if platform == "linkedin" else "casual")
    
    research_info = ""
    if research_data and research_data.get("summary"):
        research_info = f"\n\nResearch Summary:\n{research_data['summary']}"
    
    user_prompt = f"""Create a {platform} post about: {topic}

Requirements:
- Tone: {tone}
- Length: approximately {word_count} words
- Platform: {platform}
- Include relevant hashtags
- Make it engaging and shareable
{research_info}

Generate the complete post."""
    
    # Generate content
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    content = response.content
    
    # Ensure character limit
    if len(content) > config["max_chars"]:
        # Truncate if needed
        content = content[:config["max_chars"]-3] + "..."
    
    return {
        **state,
        "draft_content": content,
        "final_content": content,
    }

