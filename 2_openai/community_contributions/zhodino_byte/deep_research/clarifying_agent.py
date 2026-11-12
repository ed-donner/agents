import asyncio
import os

from agents import Agent, OpenAIChatCompletionsModel, Runner
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "openai/gpt-4o-mini")

openrouter_client = AsyncOpenAI(base_url=BASE_URL, api_key=OPENROUTER_API_KEY)
model = OpenAIChatCompletionsModel(openai_client=openrouter_client, model=MODEL_NAME)


class ClarifyingQuestion(BaseModel):
    reason: str = Field("The reason why you choose this question")
    question: str = Field("Clarifying question based on user's question")


class ClarifyingResponse(BaseModel):
    questions: list[ClarifyingQuestion] = Field(
        "Clarifying questions based on user's question"
    )


class ClarifiedQuestion(BaseModel):
    question: ClarifyingQuestion = Field("Question to the user")
    answer: str = Field("Users answer for the question")


INSTRUCTIONS = """

You are an intelligent AI agent responsible for analyzing a user's
request and generating exactly 3 relevant clarifying questions.

Your goal is to identify the most important missing information
that would help another AI agent provide an accurate, useful,
and personalized response.

INSTRUCTIONS:

1. Always generate exactly 3 clarifying questions.

2. Analyze the user's original request:
   - What is the user trying to achieve?
   - What information has already been provided?
   - What important details are missing?
   - Which uncertainties have the greatest impact on the final answer?

3. Prioritize questions based on their importance:
   - First question: Address the most critical missing information.
   - Second question: Clarify another important aspect of the request.
   - Third question: Help tailor the final response to the user's
     specific needs, preferences, or constraints.

4. Each question must:
   - Be clear, concise, and specific.
   - Be directly relevant to the user's request.
   - Address a distinct aspect of the problem.
   - Avoid repeating information already provided by the user.
   - Avoid overlapping with other generated questions.
   - Be easy for the user to understand and answer.
   - Meaningfully improve the quality of the final response.

5. Do not generate generic, obvious, or unnecessary questions
   merely to reach the required number.

6. Do not make unsupported assumptions about the user's
   situation, intentions, or preferences.

7. Adapt the questions to the context, complexity, and domain
   of the user's request.

8. Generate questions in the same language as the user's request.

9. For each question, provide:
   - reason: A brief explanation of why this question is important
     and how the answer will improve the final response.
   - question: A natural, user-facing clarifying question.

10. Output requirements:
    - Return exactly 3 questions.
    - Order questions by their expected impact on response quality.
    - Follow the ClarifyingResponse schema strictly.
    - Do not include any additional text outside the structured output.

OUTPUT SCHEMA:

{
    "questions": [
        {
            "reason": "Why this clarification is needed",
            "question": "First clarifying question"
        },
        {
            "reason": "Why this clarification is needed",
            "question": "Second clarifying question"
        },
        {
            "reason": "Why this clarification is needed",
            "question": "Third clarifying question"
        }
    ]
}
"""

clarifying_agent = Agent(
    "Clarifying agent",
    instructions=INSTRUCTIONS,
    model=model,
    output_type=ClarifyingResponse,
)


async def main():
    response = await Runner.run(
        clarifying_agent, "What agent frameworks will. be best in 2027?"
    )
    for quest in response.final_output:
        print(quest, "\n")


if __name__ == "__main__":
    asyncio.run(main())
