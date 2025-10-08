from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_CLARIFYING_QUESTIONS = 3

INSTRUCTIONS = f"""You are a research assistant. Given a query, come up with {HOW_MANY_CLARIFYING_QUESTIONS} clarifying questions 
to ask the user to better understand their research needs. These questions should help narrow down the scope and 
provide more specific context for the research. Focus on questions that explore:
- Specific aspects or angles of the topic
- Time period or recency requirements
- Geographic or industry focus
- Depth of analysis needed
- Specific outcomes or use cases

Output a list of clear, specific questions that will help refine the research query."""

class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(description=f"A list of {HOW_MANY_CLARIFYING_QUESTIONS} clarifying questions to better understand the user's research query.")

class EnhancedQuery(BaseModel):
    original_query: str = Field(description="The original user query")
    clarifying_context: str = Field(description="A summary of the clarifying questions and user responses")
    enhanced_query: str = Field(description="The enhanced search query incorporating user clarifications")

clarifying_agent = Agent(
    name="ClarifyingAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)

# Agent to process user responses and enhance the query
ENHANCE_INSTRUCTIONS = """You are a research assistant. You will be given:
1. The original user query
2. A list of clarifying questions that were asked
3. The user's responses to those questions

Your task is to create an enhanced search query that incorporates the user's clarifications. 
Combine the original query with the clarifying information to create a more specific and targeted search query.
The enhanced query should be more precise and focused based on the user's responses."""

enhance_query_agent = Agent(
    name="EnhanceQueryAgent", 
    instructions=ENHANCE_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EnhancedQuery,
)