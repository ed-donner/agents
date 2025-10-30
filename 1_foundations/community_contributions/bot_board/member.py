from typing import List, Dict, Optional
from openai import OpenAI
from conversation_context import ConversationContext
from conversation_state import ConversationState
from conversation_role import ConversationRole

def generate_user_content(prompt: Optional[str] = None) -> str:
    """Return a clear, state-specific user instruction for the LLM.

    The instruction is designed to be concise, explicit, and unambiguous so that
    different models can reliably follow it without extra context.
    """
    shared = Member.get_shared_context()
    if shared is None:
        raise RuntimeError("Shared ConversationContext is not set. Call Member.set_shared_context(...) before generating messages.")
    state = shared.get_conversation_state()

    match state:
        case ConversationState.OPEN:
            return (
                "Introduce yourself to the company’s Board of Directors: "
                "state your name, your position/role on the board, and your primary area of expertise. "
                "Keep it to 2–3 sentences and end with how you typically contribute to decisions."
            )
        
        case ConversationState.QUESTION:
            if prompt and prompt.strip():
                return (
                    "Based on the provided problem statement, write ONE high‑leverage decision question "
                    "the board should answer to make progress: "
                    f"Problem: {prompt.strip()} "
                    "Requirements:\n"
                    "- Output only the single question (no preface or explanation).\n"
                    "- Make it specific and actionable.\n"
                    "- If helpful, include constraints or success criteria within the question."
                )
            else:
                return (
                    "Write ONE high‑leverage decision question the board should answer next, "
                    "using the conversation so far.\n"
                    "Requirements:\n"
                    "- Output only the single question (no preface or explanation).\n"
                    "- Make it specific and actionable.\n"
                    "- If information is missing, phrase the question to surface the key unknowns."
                )
            
        case ConversationState.ANSWER:
            return (
                "Introduce yourself just by name.\n"
                "Answer the most recent decision question in the conversation from your role’s perspective.\n"
                "Requirements:\n"
                "- Start with a one-sentence recommendation.\n"
                "- Then provide 3–5 bullet points covering rationale, key assumptions, risks/trade‑offs, and immediate next steps.\n"
                "- Stay within the available context; do not invent facts outside it."
            )
            
        case ConversationState.EVALUATION:
            return (
                "Introduce yourself just by name.\n"
                "Evaluate the proposed answer against the question. Provide a brief, structured critique and an overall judgment.\n"
                "Structure:\n"
                "- Relevance (1–5): short justification.\n"
                "- Feasibility (1–5): short justification.\n"
                "- Risks/Trade‑offs (1–5): short justification.\n"
                "- Alignment with objectives (1–5): short justification.\n"
                "End with: Overall verdict: <one concise sentence>."
            )
            
        case ConversationState.DECISION:
            return (
                "Make a clear decision for the board based on the evaluation.\n"
                "Include:\n"
                "- Decision: <one sentence>.\n"
                "- Justification: 2–3 bullets.\n"
                "- Conditions/Assumptions: 1–2 bullets (if any).\n"
                "- Next steps: 2–3 bullets.\n"
                "- Confidence (1–5): <number>."
            )
        
        case ConversationState.SUMMARY:
            return (
                "Summarize the flow succinctly in 3–5 sentences: the question, the answer, the evaluation, and the decision. "
                "Do not add new information."
            )
        
        case ConversationState.CLOSE:
            return "Thank you for your time. This concludes the board session. Goodbye."

    # Fallback (should not happen): provide a safe, generic instruction
    return "Provide a concise, helpful response based on the conversation so far."


def get_shared_context() -> ConversationContext:
    shared = Member.get_shared_context()
    if shared is None:
        raise RuntimeError(
            "Shared ConversationContext is not set. Call Member.set_shared_context(...) before generating messages.")
    return shared

class Member:
    # Class-level shared ConversationContext reference (singleton-style)
    _shared_context: Optional[ConversationContext] = None

    @classmethod
    def set_shared_context(cls, context: ConversationContext) -> None:
        """Set a shared ConversationContext that all Member instances can access.
        Pass the same instance to make it effectively a singleton across members.
        """
        cls._shared_context = context

    @classmethod
    def get_shared_context(cls) -> Optional[ConversationContext]:
        return cls._shared_context

    def __init__(self, name, url, api_key, model, role):
        self.name = name
        self.model = model
        self.role = role
        self.client = OpenAI(api_key=api_key, base_url=url)
        self.conversation_role = ConversationRole.NONE

    def __generate_response(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content

    def __generate_system_content(self) -> str:
       return (
           f"You are {self.name}, serving as {self.role} on the company’s Board of Directors. "
           "Your task is to help the board make an important decision."
       )

    def __generate_messages(self, prompt: Optional[str] = None) -> List[Dict[str, str]]:
        context = get_shared_context().get_context()

        messages = [{"role": "system", "content": self.__generate_system_content()}]
        messages.extend(context)
        messages.append({"role": "user", "content": generate_user_content(prompt)})

        return messages

    def get_member_response(self, prompt: Optional[str] = None) -> str:
        shared = get_shared_context()

        if not shared.should_participate(self.conversation_role):
            return ""

        if prompt is None:
            prompt = shared.subject

        messages = self.__generate_messages(prompt)
        return self.__generate_response(messages)

    def set_conversation_role(self, role: ConversationRole) -> None:
        self.conversation_role = role


