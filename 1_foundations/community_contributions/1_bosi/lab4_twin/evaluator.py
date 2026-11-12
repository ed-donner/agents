"""Guardrail: a second LLM call that checks each reply stays on professional topics."""

import anthropic
from pydantic import BaseModel, Field

from context import NAME, summary

# A different model family from the twin (OpenAI), so the check is independent.
# Swap to "claude-haiku-5-5" for a faster, cheaper check.
EVALUATOR_MODEL = "claude-opus-5-5"

claude = anthropic.Anthropic()


class Evaluation(BaseModel):
    is_acceptable: bool = Field(description="True if the reply stays on professional topics, as defined in the rules")
    feedback: str = Field(description="If not acceptable, what is off-topic and how to fix it. Otherwise a short note.")


EVALUATOR_SYSTEM_PROMPT = f"""
You are a strict quality checker for an AI assistant that acts as the digital version of {NAME} on their website.

Your only job: decide whether the assistant's latest reply stays on professional topics.

Acceptable replies talk about:
- {NAME}'s career, background, education, skills, experience and projects
- recruiter screening topics such as work authorization, location, target roles and compensation
- professional opportunities, collaboration, or getting in touch (including asking for an email address)
- brief greetings or small talk that lead back to professional topics
- politely declining an off-topic request, or saying they don't know something
- a brief mention of the hobbies or preferences in the summary below, only when asked, steering back to work

Unacceptable replies:
- engage with off-topic requests (recipes, sports, politics, news, trivia, homework, unrelated code, etc.)
- go on at length about personal life, or share personal details that are not in the summary below
- drop the role of {NAME}'s digital version

Judge the reply only. A user asking something off-topic is fine, as long as the reply does not go along with it.

Here is {NAME}'s summary, so you know which personal details they are comfortable sharing:

{summary}
""".strip()


def text_of(content):
    """Gradio may give message content as a string or as a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(block.get("text", "") for block in content if isinstance(block, dict))
    return str(content)


def evaluator_user_prompt(reply, message, history):
    transcript = "\n".join(f"{h['role']}: {text_of(h['content'])}" for h in history) or "(no earlier messages)"
    return f"""Here is the conversation so far:

{transcript}

The user's latest message:
{message}

The assistant's reply to evaluate:
{reply}

Does this reply stay on professional topics? Give your verdict and feedback."""


def evaluate(reply, message, history) -> Evaluation:
    response = claude.beta.messages.parse(
        model=EVALUATOR_MODEL,
        max_tokens=4096,
        output_config={"effort": "low"},
        # If Claude declines, the API retries on a fallback model (sent raw so it works on the course's SDK version)
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
        system=EVALUATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": evaluator_user_prompt(reply, message, history)}],
        output_format=Evaluation,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"Evaluator gave no verdict (stop_reason={response.stop_reason})")
    return response.parsed_output
