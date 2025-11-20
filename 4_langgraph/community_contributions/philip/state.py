"""
State definition for Content Creation Assistant.
"""

from typing import Annotated, TypedDict, List, Any, Optional, Dict
from langgraph.graph.message import add_messages


class ContentState(TypedDict):
    """State for content creation workflow."""
    
    messages: Annotated[List[Any], add_messages]
    
    content_type: str  # "blog", "social", "seo", "research", "mixed"
    topic: str
    platform: Optional[str]  # For social media: "twitter", "linkedin", "instagram"
    
    requirements: Dict[str, Any]  # word_count, tone, style, keywords, etc.
    
    research_data: Optional[Dict[str, Any]]  # Research findings, sources
    
    # Content generation
    outline: Optional[str]  # Content outline
    draft_content: Optional[str]  # Initial draft
    final_content: Optional[str]  # Final content
    
    seo_metadata: Optional[Dict[str, Any]]  # Title, meta description, keywords
    
    # Evaluation
    feedback: Optional[str]
    success_criteria: str
    success_criteria_met: bool
    user_input_needed: bool
    evaluator_feedback: Optional[Dict[str, Any]]  # Structured feedback from evaluator
    
    # Loop prevention
    refinement_count: int  # Track how many times we've refined

