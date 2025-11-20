"""
Content refiner node - allows editing and refinement.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import ContentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


def content_refiner_node(state: ContentState) -> ContentState:
    """Refine and edit content based on feedback."""
    
    # Increment refinement counter to prevent infinite loops
    refinement_count = state.get("refinement_count", 0) + 1
    MAX_REFINEMENTS = 3
    
    # If we've exceeded max refinements, add a note and return
    if refinement_count > MAX_REFINEMENTS:
        return {
            **state,
            "refinement_count": refinement_count,
            "feedback": state.get("feedback", "") + f"\n\nNote: Maximum refinement attempts ({MAX_REFINEMENTS}) reached. Content may not fully meet all requirements.",
            "user_input_needed": True,  # Signal that we need to stop
        }
    
    feedback = state.get("feedback", "")
    draft_content = state.get("draft_content", "")
    content_type = state.get("content_type", "blog")
    requirements = state.get("requirements", {}) or {}  # Handle None case
    topic = state.get("topic", "")
    
    # Handle None case for evaluator_feedback
    evaluator_feedback = state.get("evaluator_feedback") or {}
    
    if not feedback or not draft_content:
        return {
            **state,
            "refinement_count": refinement_count,
        }
    
    word_count_met = evaluator_feedback.get("word_count_met", False)
    content_complete = evaluator_feedback.get("content_complete", False)
    needs_expansion = evaluator_feedback.get("needs_expansion", False)
    missing_topics = evaluator_feedback.get("missing_topics", [])
    specific_issues = evaluator_feedback.get("specific_issues", [])
    
    # Fallback: if structured feedback not available, check word count
    word_count = requirements.get("word_count", 1000)
    current_word_count = len(draft_content.split())
    
    # Use structured feedback if available, otherwise fallback to word count check
    if not evaluator_feedback:
        needs_expansion = current_word_count < word_count * 0.9
        content_complete = True
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    if needs_expansion:
        # Content is too short or incomplete - expand it
        system_prompt = """You are an expert content writer. Your job is to complete and expand content to meet requirements.
        
CRITICAL: You MUST generate COMPLETE content. Do not stop mid-sentence. Finish every section."""
        
        # Build structured task list from evaluator feedback
        tasks = []
        if not word_count_met:
            tasks.append(f"Expand content to meet {word_count} words (currently {current_word_count} words)")
        if not content_complete:
            tasks.append("Complete any incomplete sections")
        if missing_topics:
            tasks.append(f"Add sections on: {', '.join(missing_topics)}")
        if specific_issues:
            tasks.extend([f"Fix: {issue}" for issue in specific_issues])
        if not tasks:
            tasks.append("Expand and improve content based on feedback")
        
        tasks_str = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
        
        user_prompt = f"""The following {content_type} content needs to be completed and expanded based on structured evaluation.

Topic: {topic}
Required word count: {word_count} words
Current word count: {current_word_count} words
Content type: {content_type}
Refinement attempt: {refinement_count} of {MAX_REFINEMENTS}

STRUCTURED EVALUATION:
- Word count met: {word_count_met} (need {word_count}, have {current_word_count})
- Content complete: {content_complete}
- Needs expansion: {needs_expansion}
- Missing topics: {', '.join(missing_topics) if missing_topics else 'None'}
- Specific issues: {', '.join(specific_issues) if specific_issues else 'None'}

DETAILED FEEDBACK:
{feedback}

Current content:
{draft_content}

CRITICAL TASKS - Address ALL points:
{tasks_str}

Generate the COMPLETE, expanded content in Markdown format that addresses ALL evaluation points."""
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        refined_content = response.content
        
        return {
            **state,
            "draft_content": refined_content,
            "final_content": refined_content,
            "refinement_count": refinement_count,
        }
    else:
        # Content length is okay, refine based on feedback
        system_prompt = """You are an expert content editor. Refine content based on feedback while maintaining the core message and structure. Address ALL specific points mentioned in the feedback."""
        
        # Build task list from structured feedback
        tasks = []
        if missing_topics:
            tasks.append(f"Add sections on: {', '.join(missing_topics)}")
        if specific_issues:
            tasks.extend([f"Fix: {issue}" for issue in specific_issues])
        if not content_complete:
            tasks.append("Complete any incomplete sections")
        if not tasks:
            tasks.append("Improve content based on feedback")
        
        tasks_str = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
        
        user_prompt = f"""Refine this {content_type} content to address structured evaluation:

Topic: {topic}
Content type: {content_type}
Refinement attempt: {refinement_count} of {MAX_REFINEMENTS}

STRUCTURED EVALUATION:
- Content complete: {content_complete}
- Missing topics: {', '.join(missing_topics) if missing_topics else 'None'}
- Specific issues: {', '.join(specific_issues) if specific_issues else 'None'}

DETAILED FEEDBACK:
{feedback}

Current content:
{draft_content}

TASKS - Address ALL points:
{tasks_str}

Refine the content to address every evaluation point. Do not just make minor changes - actively fix the issues mentioned."""
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        refined_content = response.content
        
        return {
            **state,
            "draft_content": refined_content,
            "final_content": refined_content,
            "refinement_count": refinement_count,
        }

