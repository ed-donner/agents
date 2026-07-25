"""
Curriculum Builder Node - Creates structured learning milestones from research.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from state import State, CurriculumOutput


class CurriculumBuilderNode:
    """
    Build a structured curriculum from research findings.
    Creates ordered milestones with resources and project ideas.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model)
        self.llm_with_output = self.llm.with_structured_output(CurriculumOutput)
        
        self.system_prompt = """You are an expert curriculum designer. Create comprehensive, 
well-structured learning paths that guide learners from their current level to mastery.

Guidelines:
- Order milestones logically (prerequisites before advanced topics)
- Include diverse resource types (articles, videos, docs, tutorials)
- Add practical project ideas for hands-on learning
- Estimate realistic timeframes based on the user's time commitment
- Provide real, working URLs for resources when possible
- Each milestone should have 2-4 high-quality resources"""

    def execute(self, state: State) -> Dict[str, Any]:
        """Execute the curriculum builder node."""
        topic = state["topic"]
        skill_level = state["current_skill_level"]
        time_commitment = state["time_commitment"]
        prerequisites = state.get("prerequisites", [])
        key_concepts = state.get("key_concepts", [])
        research_summary = state.get("research_summary", "")
        evaluation_feedback = state.get("evaluation_feedback")
        user_prompt = f"""Create a learning path for: {topic}

User's current skill level: {skill_level}
Time commitment: {time_commitment}

Research findings:
- Prerequisites: {', '.join(prerequisites) if prerequisites else 'None identified'}
- Key concepts: {', '.join(key_concepts) if key_concepts else 'None identified'}
- Summary: {research_summary}

"""
        if evaluation_feedback:
            user_prompt += f"""
Previous feedback from evaluator (address these issues):
{evaluation_feedback}

"""

        user_prompt += """Create a structured curriculum with:
1. An overview of the learning path
2. 4-6 milestones covering prerequisites to advanced topics
3. Each milestone should have:
   - Clear title and goal
   - 2-4 learning resources with real URLs
   - A hands-on project idea
   - Estimated days to complete

Ensure the curriculum:
- Starts with foundational knowledge if needed
- Progresses logically through concepts
- Includes practical application at each stage
- Is achievable within the user's time commitment"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        result = self.llm_with_output.invoke(messages)
        return {
            "curriculum": result,
            "messages": [{"role": "assistant", "content": f"Curriculum created with {len(result.milestones)} milestones. Estimated completion: {result.total_estimated_days} days."}]
        }
