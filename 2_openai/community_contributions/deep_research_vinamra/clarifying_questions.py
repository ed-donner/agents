from pydantic import BaseModel, Field
from agents import Agent,Runner
from typing import List
from model_config import mimo_model


class ClarifyingQuestions(BaseModel):
    """Collection of clarifying questions"""
    should_ask: bool = Field(
        description="Whether these questions would significantly improve the research"
    )
    confidence_score: float = Field(
        description="Confidence that the current query is clear enough (0-1)"
    )
    questions: List[str] = Field(
        description="List of 3 clarifying questions to improve research quality"
    )


CLARIFYING_INSTRUCTIONS = """You are a research assistant that helps improve research queries.

Given a research query, analyze whether it needs clarification and generate exactly 3 helpful 
clarifying questions that would improve the research quality.

Consider these aspects:
1. **Scope**: Is the topic too broad or too narrow? 
   Example: "AI" → "Are you interested in AI applications in healthcare, or AI ethics?"

2. **Depth**: What level of detail is needed?
   Example: "quantum computing" → "Do you need a beginner overview or technical deep-dive?"

3. **Focus**: What specific aspect interests them most?
   Example: "climate change" → "Are you focused on causes, impacts, or solutions?"

4. **Format**: What type of output would be most useful?
   Example: "startup funding" → "Do you need statistics, case studies, or practical advice?"

Return a JSON object with these exact fields:
- should_ask (boolean): True if the query is vague/ambiguous and would benefit from clarification
- confidence_score (float): How clear the query is (1.0 = very clear, 0.0 = very ambiguous)
- questions (array of strings): Exactly 3 clarifying questions

Always generate 3 questions, but mark should_ask=false if the query is already sufficiently clear.
"""

clarifying_agent = Agent(
    name="ClarifyingAgent",
    instructions=CLARIFYING_INSTRUCTIONS,
    model=mimo_model,
    output_type=ClarifyingQuestions,
)


class ClarifyingQuestionsTool:
    """Tool to generate and handle clarifying questions"""
    
    CONFIDENCE_THRESHOLD = 0.7  # Below this, we should ask questions
    
    @staticmethod
    async def generate_questions(query: str) -> ClarifyingQuestions:
        """
        Generate clarifying questions for a research query
        
        Args:
            query: The user's research query
            
        Returns:
            ClarifyingQuestions object with 3 questions and metadata
        """
        
        result = await Runner.run(
            clarifying_agent,
            f"Research Query: {query}",
        )
        
        return result.final_output_as(ClarifyingQuestions)
    
    @staticmethod
    def should_ask_questions(clarifying_result: ClarifyingQuestions) -> bool:
        """
        Determine if we should actually ask the clarifying questions
        
        Args:
            clarifying_result: Result from generate_questions
            
        Returns:
            True if questions should be presented to user
        """
        return (
            clarifying_result.should_ask and 
            clarifying_result.confidence_score < ClarifyingQuestionsTool.CONFIDENCE_THRESHOLD
        )
    
    @staticmethod
    def format_questions_for_ui(questions: ClarifyingQuestions) -> str:
        """
        Format clarifying questions for display in UI
        
        Args:
            questions: ClarifyingQuestions object
            
        Returns:
            Formatted string for display
        """
        if not questions.should_ask:
            return ""
        
        output = "## 🤔 Clarifying Questions\n\n"
        output += "To provide better research results, please help clarify:\n\n"
        
        for i, q in enumerate(questions.questions, 1):
            output += f"**{i}.** {q}\n\n"
        
        return output
    
    @staticmethod
    def refine_query_with_answers(
        original_query: str, 
        questions: List[str],
        answers: List[str]
    ) -> str:
        """
        Combine original query with answers to clarifying questions
        
        Args:
            original_query: Original research query
            questions: List of clarifying questions
            answers: User's answers to the questions
            
        Returns:
            Refined query incorporating the answers
        """
        refined = f"{original_query}\n\nAdditional Context:\n"
        
        for q, a in zip(questions, answers):
            if a and a.strip():
                refined += f"- {q} → {a}\n"
        
        return refined
