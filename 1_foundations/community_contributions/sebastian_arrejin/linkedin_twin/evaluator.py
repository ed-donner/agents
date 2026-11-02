from openai import OpenAI
from pydantic import BaseModel, Field
from config import EVALUATOR_MODEL, IDENTITY, NAME


class Evaluation(BaseModel):
    is_grounded: bool = Field(description="True if every factual claim about the person is supported by the evidence")
    is_formal: bool = Field(description="True if the tone is formal and professional")
    is_on_topic: bool = Field(description="True if the reply stays on professional topics or politely redirects")
    unsupported_claims: list[str] = Field(description="Each claim in the reply, or in the Q&A pairs to save, that the evidence does not support")
    feedback: str = Field(description="Concrete instructions for the agent to fix the reply; empty if acceptable")

    @property
    def is_acceptable(self):
        return self.is_grounded and self.is_formal and self.is_on_topic


EVALUATOR_SYSTEM_PROMPT = f"""
You are a strict quality reviewer for an AI digital twin of {NAME}, deployed on his professional website.
The twin answers visitors' questions about {NAME}'s career. You decide whether its latest reply can be shown to the visitor.

Check three things:

1. Grounding (most important). Every factual statement about {NAME} (employers, roles, dates, years of experience, skills,
tools, certifications, education, projects, languages, availability, salary, opinions) must be directly supported by the EVIDENCE section.
- Facts mentioned in earlier turns of the conversation are NOT evidence.
- Saying that the information is not available is always acceptable.
- Reasonable paraphrases and summaries of the evidence are acceptable; extrapolations are not
  (e.g. "8 years with Cypress" when the evidence only lists Cypress as a skill).
- General explanations that are not about {NAME} (e.g. what ISTQB is) are acceptable if correct and not presented as facts about him.
- Confirmations of actions (e.g. "I have recorded your email") are acceptable only if the action appears in ACTIONS PERFORMED.
- The same rules apply to any Q&A pair the twin wants to save to the FAQ database.

2. Formality. The reply must be courteous, formal and professional, as if addressing a recruiter or a client.
In Spanish it must use "usted", never "tú" or "vos". No slang, no emojis, no exaggerated enthusiasm.

3. Scope. The reply must stay on professional topics (career, skills, experience, getting in touch)
or politely steer the conversation back to them.

An empty reply, or one that does not address the visitor's message, is never acceptable.
Be strict: if in doubt about a claim, list it in unsupported_claims and mark the reply as not grounded.
""".strip()


def format_history(history):
    if not history:
        return "(no previous messages)"
    return "\n".join(f"{message['role']}: {message['content']}" for message in history)


def evaluate(client: OpenAI, reply, message, history, evidence, actions, pending_faqs) -> Evaluation:
    evidence_text = "\n\n".join([f"[Identity]\n{IDENTITY}", *evidence])
    actions_text = "\n".join(actions) or "(none)"
    faqs_text = "\n".join(f"Q: {question}\nA: {answer}" for question, answer in pending_faqs) or "(none)"
    user_prompt = f"""
## Conversation so far
{format_history(history)}

## Latest message from the visitor
{message}

## Reply to evaluate
{reply}

## EVIDENCE (everything the twin retrieved for this reply)
{evidence_text}

## ACTIONS PERFORMED
{actions_text}

## Q&A pairs the twin wants to save to the FAQ database
{faqs_text}
""".strip()
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = client.chat.completions.parse(model=EVALUATOR_MODEL, messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed
