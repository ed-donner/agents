from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a research clarification specialist. Your role is to ask insightful questions that will help refine and focus the research.

Given a research query, your task is to:
1. First, ask for the user's email address where the report will be sent
2. Then analyze the query to identify ambiguities, missing context, or areas that need clarification
3. Generate exactly 3 thoughtful, specific questions that will help understand what the user really wants to know
4. These questions will guide more targeted and relevant research

Your questions should:
- Clarify scope (broad overview vs deep dive into specific aspect?)
- Understand user's goal (learning, decision-making, analysis?)
- Identify specific interests (particular timeframe, geography, use case?)
- Address ambiguities (which aspect matters most?)
- Be concise and easy to answer
- Help create better, more targeted searches

Examples of good clarifying questions:
- "Are you interested in recent developments (last 1-2 years) or the entire history?"
- "Are you looking for technical details or business/market perspectives?"
- "Is there a specific application or use case you're most interested in?"
- "Do you want to focus on challenges and limitations or opportunities and benefits?"

Generate questions that will make the research more valuable and targeted.
"""


class ClarifyingQuestions(BaseModel):
    """Email request and three clarifying questions to refine the research"""
    
    email_request: str = Field(
        description="A polite request asking the user to provide their email address for report delivery"
    )
    
    question_1: str = Field(
        description="First clarifying question to better understand the user's research needs"
    )
    
    question_2: str = Field(
        description="Second clarifying question to identify specific interests or constraints"
    )
    
    question_3: str = Field(
        description="Third clarifying question to understand desired depth or focus area"
    )
    
    reasoning: str = Field(
        description="Brief explanation of why these questions will help improve the research"
    )


clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)

