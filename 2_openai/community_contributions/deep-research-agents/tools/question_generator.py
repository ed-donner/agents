from schema import Question
from tools.tool_wrapper import tool_from_agent


# Instructions for the QuestionGenerator
QUESTION_GENERATOR_INSTRUCTIONS = """
Role:
- You are a helpful research assistant.

Task:
- Conducting an interactive questioning session.

Input:
- The user input will be a ResearchContext JSON string.

Steps:
1) Parse the JSON from the user message to get the initial_query and qa_history.
2) If qa_history is empty:
   - Ask the very first clarifying question (5–50 words) that best frames the user’s initial_query.
3) If qa_history is not empty:
   - Identify the highest-utility remaining uncertainty given qa_history.
   - Ask ONE concrete follow-up question (5–50 words) that reduces that uncertainty.
   - Do NOT repeat or rephrase any prior question.
4) Fill 'reasoning' with a concise, non-sensitive justification (1 sentence).

Output:
- A Question schema.
"""

question_generator_tool = tool_from_agent(
    agent_name="QuestionGenerator",
    agent_instructions=QUESTION_GENERATOR_INSTRUCTIONS,
    output_type=Question,
    tool_name="generate_question",
    tool_description="Ask a follow-up question based on previous context and user answers"
)
