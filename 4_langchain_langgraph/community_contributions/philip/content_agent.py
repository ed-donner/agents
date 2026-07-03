"""
Content Creation Agent - Main agent class.
"""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import uuid
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load environment variables (including LangSmith config)
load_dotenv()

from state import ContentState
from nodes import (
    content_type_router,
    research_node,
    blog_generator_node,
    social_generator_node,
    seo_optimizer_node,
    content_refiner_node,
)


class EvaluatorOutput(BaseModel):
    """Evaluator output schema with structured feedback."""
    feedback: str = Field(description="Detailed feedback on the generated content")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )
    # Structured feedback details
    word_count_met: bool = Field(description="Whether the content meets the required word count")
    content_complete: bool = Field(description="Whether the content is complete (no incomplete sections)")
    quality_score: int = Field(description="Quality score from 1-10", ge=1, le=10)
    missing_topics: List[str] = Field(
        default_factory=list,
        description="List of topics or areas that should be added to improve the content"
    )
    needs_expansion: bool = Field(
        description="Whether the content needs to be expanded (word count, completeness, or depth)"
    )
    specific_issues: List[str] = Field(
        default_factory=list,
        description="List of specific issues that need to be addressed"
    )


class ContentAgent:
    """Content Creation Agent with LangGraph."""
    
    def __init__(self):
        self.graph = None
        self.memory = MemorySaver()
        self.agent_id = str(uuid.uuid4())
        self.evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = self.evaluator_llm.with_structured_output(EvaluatorOutput)
    
    def evaluator(self, state: ContentState) -> ContentState:
        """Evaluate if content meets success criteria."""
        content = state.get("final_content", "")
        content_type = state.get("content_type", "")
        success_criteria = state.get("success_criteria", "Content should be high quality and meet requirements")
        
        if not content:
            return {
                **state,
                "feedback": "No content generated yet.",
                "success_criteria_met": False,
                "user_input_needed": True,
            }
        
        system_message = """You are a content quality evaluator. Assess whether the generated content meets the success criteria and requirements."""
        
        word_count = state.get('requirements', {}).get('word_count', 1000)
        actual_word_count = len(content.split())
        
        refinement_count = state.get("refinement_count", 0)
        MAX_REFINEMENTS = 3
        
        content_display = content
        if len(content) > 20000:
            # Show first 15000 chars + note, so evaluator can still assess completeness
            content_display = content[:15000] + f"\n\n[... content continues, total length: {len(content)} characters, {actual_word_count} words ...]\n\n[Note: This is a length indicator only. Check if the content above ends naturally and completely.]"
        
        user_message = f"""Evaluate this {content_type} content and provide structured feedback:

FULL COMPLETE CONTENT (this is the entire generated content, not a preview):
{content_display}

Content Statistics:
- Total length: {len(content)} characters
- Actual word count: {actual_word_count} words
- Required word count: {word_count} words
- Refinement attempts: {refinement_count} / {MAX_REFINEMENTS}

Success Criteria:
{success_criteria}

Requirements:
{state.get('requirements', {})}

Provide structured evaluation:
1. Does the content meet the success criteria? (success_criteria_met)
   CRITICAL: success_criteria_met should be FALSE if:
   - Word count is not met (word_count_met = false)
   - Content is incomplete (content_complete = false)
   - Content needs expansion (needs_expansion = true)
   - There are missing topics or specific issues
   Only set to TRUE if ALL criteria are met AND content is complete and satisfactory.

2. Does it meet the word count requirement? (word_count_met: Required {word_count}, Actual {actual_word_count})
   - TRUE only if actual word count is within 10% of required (e.g., 1350-1650 for 1500 required)

3. Is the content complete? (content_complete: Check if it ends properly, no incomplete sections, has conclusion)
   - IMPORTANT: The content above is the FULL content - check if it ends naturally and completely
   - TRUE only if content has proper ending, conclusion, and all sections are finished
   - Do NOT mark as incomplete just because you see "[... content continues]" - that's just a length indicator for very long content
   - Check the actual ending of the content to determine if it's complete

4. Quality score 1-10 (quality_score: Rate overall quality)

5. What topics or areas are missing that should be added? (missing_topics: e.g., ["patient diagnostics", "telemedicine"])
   - List specific topics mentioned in feedback or that would improve the content

6. Does it need expansion? (needs_expansion: true if word count short, incomplete, or lacks depth)
   - TRUE if word count not met, content incomplete, or feedback suggests more depth needed

7. List specific issues to address (specific_issues: e.g., ["Section on X is incomplete", "Missing discussion of Y"])
   - List concrete issues from the feedback

8. Is more user input needed? (user_input_needed: true only if truly stuck and can't improve automatically)
   - TRUE only if content cannot be improved without user clarification

IMPORTANT LOGIC:
- If word_count_met = false OR content_complete = false OR needs_expansion = true, then success_criteria_met MUST be false
- success_criteria_met = true ONLY when content fully meets all requirements and is complete

Note: If refinement attempts ({refinement_count}) are at maximum ({MAX_REFINEMENTS}), you may be more lenient, but still be accurate."""
        
        from langchain_core.messages import SystemMessage, HumanMessage
        
        eval_result = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])
        
        return {
            **state,
            "feedback": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
            # Store structured feedback in requirements for refiner to use
            "evaluator_feedback": {
                "word_count_met": eval_result.word_count_met,
                "content_complete": eval_result.content_complete,
                "quality_score": eval_result.quality_score,
                "missing_topics": eval_result.missing_topics,
                "needs_expansion": eval_result.needs_expansion,
                "specific_issues": eval_result.specific_issues,
            }
        }
    
    def route_after_evaluation(self, state: ContentState) -> str:
        """Route after evaluation with loop prevention."""
        MAX_REFINEMENTS = 3  # Maximum number of refinement attempts
        
        refinement_count = state.get("refinement_count", 0)
        success_criteria_met = state.get("success_criteria_met", False)
        user_input_needed = state.get("user_input_needed", False)
        
        # Get structured feedback to make routing decisions
        evaluator_feedback = state.get("evaluator_feedback") or {}
        needs_expansion = evaluator_feedback.get("needs_expansion", False)
        content_complete = evaluator_feedback.get("content_complete", True)
        word_count_met = evaluator_feedback.get("word_count_met", True)
        has_issues = bool(evaluator_feedback.get("specific_issues") or evaluator_feedback.get("missing_topics"))
        
        if success_criteria_met and content_complete and word_count_met and not needs_expansion:
            return "END"
        
        # If we've exceeded max refinements, end to prevent infinite loop
        if refinement_count >= MAX_REFINEMENTS:
            return "END"
        
        # If content needs work (expansion, incomplete, issues), refine it
        if needs_expansion or not content_complete or not word_count_met or has_issues:
            return "refiner"
        
        # If user input needed BUT we haven't tried refining yet, try once more
        if user_input_needed and refinement_count < MAX_REFINEMENTS:
            return "refiner"
        
        # If user input needed and we've tried enough, end
        if user_input_needed:
            return "END"
        
        # If success criteria not met, try refining
        if not success_criteria_met:
            return "refiner"
        
        # Default: end (shouldn't reach here)
        return "END"
    
    def route_by_content_type(self, state: ContentState) -> str:
        """Route based on content type."""
        content_type = state.get("content_type", "blog")
        
        if content_type == "blog":
            return "blog_generator"
        elif content_type == "social":
            return "social_generator"
        elif content_type == "seo":
            return "seo_optimizer"
        elif content_type == "research":
            return "END"  # Research only, no generation
        else:
            return "blog_generator"  # Default
    
    async def build_graph(self):
        """Build the LangGraph."""
        graph_builder = StateGraph(ContentState)
        
        # Add nodes
        graph_builder.add_node("router", content_type_router)
        graph_builder.add_node("research", research_node)
        graph_builder.add_node("blog_generator", blog_generator_node)
        graph_builder.add_node("social_generator", social_generator_node)
        graph_builder.add_node("seo_optimizer", seo_optimizer_node)
        graph_builder.add_node("refiner", content_refiner_node)
        graph_builder.add_node("evaluator", self.evaluator)
        
        # Add edges
        graph_builder.add_edge(START, "router")
        
        # Route to research first
        graph_builder.add_edge("router", "research")
        
        # After research, route to appropriate generator
        graph_builder.add_conditional_edges(
            "research",
            self.route_by_content_type,
            {
                "blog_generator": "blog_generator",
                "social_generator": "social_generator",
                "seo_optimizer": "seo_optimizer",
                "END": END,
            }
        )
        
        # All generators go to evaluator
        graph_builder.add_edge("blog_generator", "evaluator")
        graph_builder.add_edge("social_generator", "evaluator")
        graph_builder.add_edge("seo_optimizer", "evaluator")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_after_evaluation,
            {
                "refiner": "refiner",
                "END": END,
            }
        )
        graph_builder.add_edge("refiner", "evaluator")
        
        # Compile
        self.graph = graph_builder.compile(checkpointer=self.memory)
    
    async def run(self, message: str, success_criteria: str = "Content should be high quality and meet all requirements") -> Dict[str, Any]:
        """Run the content creation agent."""
        if not self.graph:
            await self.build_graph()
        
        config = {
            "configurable": {"thread_id": self.agent_id},
            "tags": ["content-creation", "langgraph"],
            "metadata": {
                "content_type": "unknown",  # Will be updated by router
                "message_length": len(message),
            }
        }
        
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "content_type": "",
            "topic": "",
            "platform": None,
            "requirements": {},
            "research_data": None,
            "outline": None,
            "draft_content": None,
            "final_content": None,
            "seo_metadata": None,
            "feedback": None,
            "success_criteria": success_criteria,
            "success_criteria_met": False,
            "user_input_needed": False,
            "evaluator_feedback": None,  # Will be populated by evaluator
            "refinement_count": 0,  # Initialize refinement counter
        }
        
        result = await self.graph.ainvoke(initial_state, config=config)
        return result

