import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from context import summary, linkedin

load_dotenv(override=True)

EVALUATOR_MODEL = "gemini-2.5-flash"


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


evaluator_system_prompt = f"""You evaluate replies from a digital twin chatting with website visitors.
Decide if the latest reply is acceptable: professional, engaging, on-topic, and factually consistent
with the context below. It must not make anything up.
Reject replies that quote prices, make commitments, or promise anything on Lamin's behalf
that isn't supported by the context.

## Summary:
{summary}

## LinkedIn:
{linkedin}
"""


def evaluator_user_prompt(reply, message, history):
    return f"""Conversation so far:
{history}

Latest user message:
{message}

Twin's reply:
{reply}

Evaluate the reply and give feedback."""


google_api_key = os.getenv("GOOGLE_API_KEY")
print("Google key found" if google_api_key else "Google key NOT found")

gemini = OpenAI(
    api_key=google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


def evaluate(reply, message, history) -> Evaluation:
    messages = [
        {"role": "system", "content": evaluator_system_prompt},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = gemini.chat.completions.parse(
        model=EVALUATOR_MODEL, messages=messages, response_format=Evaluation
    )
    return response.choices[0].message.parsed