"""
Evaluator Node - Validates the curriculum for completeness and quality.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from state import State, EvaluatorOutput


MAX_REVISIONS = 2


class EvaluatorNode:
    """
    Evaluate the curriculum for completeness, logical ordering, and quality.
    Decides if it's ready or needs revision.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", max_revisions: int = MAX_REVISIONS):
        self.max_revisions = max_revisions
        self.llm = ChatOpenAI(model=model)
        self.llm_with_output = self.llm.with_structured_output(EvaluatorOutput)
        
        self.system_prompt = """You are a curriculum quality evaluator. Your job is to assess 
learning paths and determine if they meet quality standards.

Evaluation criteria:
1. Logical ordering - prerequisites come before advanced topics
2. Resource quality - diverse types, appropriate difficulty levels
3. Completeness - covers all key concepts identified in research
4. Practical application - includes hands-on projects
5. Realistic timeline - achievable within user's time commitment
6. Clear progression - each phase builds on previous ones

Be constructive in your feedback. If issues exist, clearly explain what needs improvement."""

    def execute(self, state: State) -> Dict[str, Any]:
        """Execute the evaluator node."""
        topic = state["topic"]
        skill_level = state["current_skill_level"]
        time_commitment = state["time_commitment"]
        prerequisites = state.get("prerequisites", [])
        key_concepts = state.get("key_concepts", [])
        curriculum = state.get("curriculum")
        revision_count = state.get("revision_count", 0)
        
        if not curriculum:
            return {
                "evaluation_feedback": "No curriculum to evaluate.",
                "is_complete": False,
                "needs_user_input": True,
                "messages": [{"role": "assistant", "content": "Evaluation failed: No curriculum provided."}]
            }
        
        curriculum_text = f"""Overview: {curriculum.overview}
Total Duration: {curriculum.total_estimated_days} days

Milestones:
"""
        for m in curriculum.milestones:
            curriculum_text += f"""
Phase {m.phase_number}: {m.title}
- Goal: {m.goal}
- Description: {m.description}
- Resources: {len(m.resources)} items
- Project: {m.project_idea or 'None'}
- Duration: {m.estimated_days} days
"""

        user_prompt = f"""Evaluate this learning path for: {topic}

User context:
- Current skill level: {skill_level}
- Time commitment: {time_commitment}

Research identified:
- Prerequisites: {', '.join(prerequisites) if prerequisites else 'None'}
- Key concepts: {', '.join(key_concepts) if key_concepts else 'None'}

Curriculum to evaluate:
{curriculum_text}

Assess this curriculum against the quality criteria:
1. Does it have logical ordering (prerequisites before advanced)?
2. Are resources diverse and appropriate?
3. Does it cover all key concepts?
4. Are there practical projects?
5. Is the timeline realistic for {time_commitment}?
6. Is there clear progression between phases?

Provide your evaluation with:
- Detailed feedback on strengths and weaknesses
- Whether it meets quality standards (is_complete)
- Whether user clarification is needed (needs_user_input)
- Specific issues to address (if any)"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        result = self.llm_with_output.invoke(messages)
        
        new_revision_count = revision_count + 1
        
        # Force approval after max revisions to prevent infinite loops
        if not result.is_complete and new_revision_count >= self.max_revisions:
            return {
                "evaluation_feedback": f"{result.feedback}\n\n[Auto-approved after {self.max_revisions} revisions]",
                "is_complete": True,
                "needs_user_input": False,
                "revision_count": new_revision_count,
                "messages": [{"role": "assistant", "content": f"Evaluation complete: auto-approved after {self.max_revisions} revision(s)."}]
            }
        
        status = "approved" if result.is_complete else "needs revision"
        
        return {
            "evaluation_feedback": result.feedback,
            "is_complete": result.is_complete,
            "needs_user_input": result.needs_user_input,
            "revision_count": new_revision_count,
            "messages": [{"role": "assistant", "content": f"Evaluation complete: {status}. {len(result.issues or [])} issues found."}]
        }
