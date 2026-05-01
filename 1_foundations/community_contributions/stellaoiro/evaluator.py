"""
HALI — HPV Awareness & Learning Initiative
Evaluator and rerun logic (Lab 3 pattern).
"""

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from prompts import EVALUATOR_SYSTEM_PROMPT
from tools import TOOLS

load_dotenv(override=True)
client = OpenAI()


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluate(reply: str, message: str, history: list) -> Evaluation:
    """
    Use a second model call to evaluate a reply for accuracy,
    cultural appropriateness, and tone before returning it to the user.
    """
    eval_messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Conversation so far:\n{history}\n\n"
                f"User said: {message}\n\n"
                f"Agent replied:\n{reply}\n\n"
                "Evaluate this response."
            ),
        },
    ]
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=eval_messages,
        response_format=Evaluation,
    )
    return response.choices[0].message.parsed


def rerun(reply: str, message: str, history: list, feedback: str, system_prompt: str) -> str:
    """Retry with the evaluator's rejection reason injected into the system prompt."""
    updated_prompt = (
        system_prompt
        + f"\n\n## Quality Control Rejection\n"
        f"Your previous reply was rejected.\n"
        f"Your attempt:\n{reply}\n\n"
        f"Reason rejected:\n{feedback}\n\n"
        "Please try again, directly addressing the feedback."
    )
    messages = (
        [{"role": "system", "content": updated_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
    )
    return response.choices[0].message.content
