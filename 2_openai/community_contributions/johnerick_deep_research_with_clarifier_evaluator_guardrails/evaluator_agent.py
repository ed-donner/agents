from dotenv import load_dotenv
import os
from openai import  AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_default_openai_client, set_default_openai_api
from pydantic import BaseModel


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

load_dotenv(override=True)

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1"

client = AsyncOpenAI(api_key=openrouter_api_key, base_url=openrouter_url)
gemini_model = OpenAIChatCompletionsModel(model="google/gemini-2.5-flash", openai_client=client)

evaluator_system_prompt = """
You are a strict evaluator with PhD-level expertise across multiple domains.

Your role is to assess whether an AI-generated response meets the standard of a high-quality, expert-level answer.

A high-quality response must be:
- accurate and free from hallucinations
- directly relevant to the question
- complete, addressing all key aspects of the query
- sufficiently deep and non-generic
- clear, well-structured, and logically sound
- useful to a knowledgeable reader

--- EVALUATION STANDARD ---

Reject the response if it:
- contains incorrect or unverifiable claims
- is incomplete or misses important aspects
- is shallow, vague, or generic
- includes unnecessary filler or fluff
- is poorly structured or hard to follow

--- INSTRUCTIONS ---

- Be strict and critical. Do not accept mediocre responses.
- Prioritize correctness, completeness, and depth over style.
- If the response is unacceptable, clearly explain what is wrong and how to fix it.
- Feedback must be specific and actionable, not general.

You must follow the required output format exactly.
"""

def evaluator_user_prompt(reply: str, message: str, history: str):
    return f"""
--- CONTEXT ---

User query:
{message}

Agent response:
{reply}

Conversation history:
{history}

--- TASK ---

Evaluate whether the response meets the required quality standard.
Reject if it is incomplete, inaccurate, or lacks depth.

--- OUTPUT FORMAT (STRICT JSON) ---

{{
  "is_acceptable": true | false,
  "feedback": "specific, actionable feedback"
}}
"""

evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=evaluator_system_prompt,
    model=gemini_model,
    output_type=Evaluation,
)
