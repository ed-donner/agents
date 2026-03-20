from __future__ import annotations

import os
from typing import Any

from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

openai_api_key = os.getenv("OPENAI_API_KEY")

if openrouter_api_key:
    evaluator_client = OpenAI(api_key=openrouter_api_key, base_url="https://openrouter.ai/api/v1")
else:
    evaluator_client = OpenAI()


def evaluator_system_prompt(name: str, summary: str, linkedin: str) -> str:
    prompt = (
        f"You are an evaluator that decides whether a response to a question is acceptable. "
        "You are provided with a conversation between a User and an Agent. "
        "Your task is to decide whether the Agent's latest response is acceptable quality. "
        f"The Agent is playing the role of {name} and is representing {name} on their website. "
        "The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        f"The Agent has been provided with context on {name} in the form of their summary and LinkedIn details. Here's the information:"
    )

    prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
    prompt += "With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback regarding the response."
    return prompt


def evaluator_user_prompt(reply: str, message: str, history: Any) -> str:
    # function to convert the history into a readable format
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluate(reply: str, message: str, history: Any, name: str, summary: str, linkedin: str) -> Evaluation:
    # function to evaluate the agent's response using the evaluator model
    messages = [
        {"role": "system", "content": evaluator_system_prompt(name, summary, linkedin)},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = evaluator_client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=Evaluation,
    )
    return response.choices[0].message.parsed


def rerun(reply: str, message: str, history: Any, feedback: str, system_prompt: str) -> str:
    # function to rerun the agent with the feedback from the evaluator, by updating the system prompt with the feedback and previous answer, and then prompting the agent to try again
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = OpenAI().chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content or ""
