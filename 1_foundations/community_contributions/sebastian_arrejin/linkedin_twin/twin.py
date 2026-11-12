from openai import OpenAI
import database
from config import IDENTITY, MAX_EVALUATION_RETRIES, MODEL, NAME
from evaluator import Evaluation, evaluate
from knowledge_base import KnowledgeBase
from tools import ToolRunner, tools

TWIN_SYSTEM_PROMPT = f"""
# Your role

You are the AI digital twin of {NAME}, running on his professional website and chatting with its visitors:
recruiters, potential clients and colleagues. You answer questions about his career, background, skills and experience,
speaking in the first person as {NAME}. If asked, explain clearly that you are an AI digital twin of {NAME}.

# Identity (always true)

{IDENTITY}

# How to answer

1. For any question about career, experience, skills, certifications, education or availability, first call search_faq,
then call search_knowledge_base (several times with different queries if useful). Do this on every turn, even if the topic
came up earlier in the conversation, because every reply is fact-checked only against what you retrieve for it.
2. Only state facts found in the identity section or in your tool results. Never invent employers, dates, job titles,
numbers, projects or opinions, and do not extrapolate (a listed skill does not tell you how many years it was used).
3. If the information is not available, say so courteously, call record_unknown_question, and offer to put the visitor
in touch with {NAME}.
4. When you answer a question that other visitors are likely to ask, call save_faq with a short, general version of the
question and your answer.
5. If the visitor wants to get in touch, ask for their email address and record it with record_user_details.

# Tone

Always formal, courteous and professional, as if speaking to a recruiter or a client.
Reply in the visitor's language. In Spanish, always address the visitor as "usted".
No emojis, no slang, no exaggerated enthusiasm. Be concise; you may use markdown, but no code blocks.

# Scope

Only discuss professional topics. If the visitor asks about something unrelated, politely steer the conversation back.
""".strip()

FALLBACK_REPLY = (
    "Le pido disculpas, pero no dispongo de información verificada para responder con precisión a esa consulta. "
    f"He registrado su pregunta para que {NAME} pueda responderla personalmente.\n\n"
    "I apologize, but I do not have verified information to answer that question accurately. "
    f"I have recorded it so that {NAME} can answer it personally."
)


EMPTY_REPLY_EVALUATION = Evaluation(
    is_grounded=False,
    is_formal=False,
    is_on_topic=False,
    unsupported_claims=[],
    feedback="The reply was empty. After using your tools, always write a complete answer for the visitor.",
)


def normalize_history(history):
    """Keep only role and text content: Gradio adds extra keys and may send content as a list of parts."""
    messages = []
    for item in history:
        content = item.get("content")
        if isinstance(content, list):
            content = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
        if isinstance(content, str) and content:
            messages.append({"role": item["role"], "content": content})
    return messages


def rejection_note(reply, evaluation):
    claims = "\n".join(f"- {claim}" for claim in evaluation.unsupported_claims) or "- (none listed)"
    return f"""

# Previous answer rejected

A quality reviewer rejected your previous reply. Write a new reply that fixes the problems.
If a fact cannot be verified with your tools, remove it or say you don't have that information.

## Your rejected reply
{reply}

## Unsupported claims
{claims}

## Reviewer feedback
{evaluation.feedback}
"""


def format_review(attempts):
    lines = ["### Evaluator review"]
    for number, evaluation in enumerate(attempts, start=1):
        verdict = "Approved" if evaluation.is_acceptable else "Rejected"
        lines.append(f"**Attempt {number}: {verdict}**")
        lines.append(
            f"- Grounded in evidence: {'yes' if evaluation.is_grounded else 'no'}"
            f" | Formal: {'yes' if evaluation.is_formal else 'no'}"
            f" | On topic: {'yes' if evaluation.is_on_topic else 'no'}"
        )
        for claim in evaluation.unsupported_claims:
            lines.append(f"- Unsupported claim: {claim}")
        if evaluation.feedback:
            lines.append(f"- Feedback: {evaluation.feedback}")
    if not attempts[-1].is_acceptable:
        lines.append("**No attempt was approved, so a safe fallback reply was shown.**")
    return "\n".join(lines)


class Twin:

    def __init__(self):
        self.openai = OpenAI()
        database.init_db()
        self.knowledge = KnowledgeBase(self.openai)

    def run_agent(self, system_prompt, history, message, runner):
        messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        while response.choices[0].finish_reason == "tool_calls":
            reply = response.choices[0].message
            messages.append(reply)
            messages.extend(runner.handle_tool_calls(reply.tool_calls))
            response = self.openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        return response.choices[0].message.content or ""

    def chat(self, message, history):
        history = normalize_history(history)
        system_prompt = TWIN_SYSTEM_PROMPT
        attempts = []
        for _ in range(MAX_EVALUATION_RETRIES + 1):
            runner = ToolRunner(self.knowledge)
            reply = self.run_agent(system_prompt, history, message, runner)
            if reply.strip():
                evaluation = evaluate(
                    self.openai, reply, message, history, runner.evidence, runner.actions, runner.pending_faqs
                )
            else:
                evaluation = EMPTY_REPLY_EVALUATION
            attempts.append(evaluation)
            print(f"Evaluation: {evaluation.model_dump()}", flush=True)
            if evaluation.is_acceptable:
                runner.commit()
                return reply, format_review(attempts)
            system_prompt = TWIN_SYSTEM_PROMPT + rejection_note(reply, evaluation)

        runner.commit(include_faqs=False)
        if not runner.pending_unknown_questions:
            database.record_unknown_question(message)
        return FALLBACK_REPLY, format_review(attempts)
