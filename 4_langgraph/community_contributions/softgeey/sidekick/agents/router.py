"""Router node: classifies the user's message into a known intent."""

from langchain_core.messages import HumanMessage
from llm_client import get_llm
from agents.state import AgentState

INTENTS = ["email", "calendar", "tasks", "research", "general"]

ROUTER_PROMPT = """You are a routing assistant. Classify the user's latest message into exactly one of these intents:

- email      : drafting, reading, or replying to emails
- calendar   : upcoming meetings, scheduling, meeting prep
- tasks      : project tracking, task management, status updates
- research   : web research, competitive intel, market analysis
- general    : anything else (general Q&A, advice, writing help)

Reply with ONLY the intent word. No explanation.

User message: {message}
"""


def router_node(state: AgentState) -> dict:
    """Classify the latest human message and set state.intent."""
    last_human = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
    )
    if not last_human:
        return {"intent": "general"}

    llm = get_llm(temperature=0.0)
    prompt = ROUTER_PROMPT.format(message=last_human.content)
    result = llm.invoke(prompt)
    intent = result.content.strip().lower()

    if intent not in INTENTS:
        intent = "general"

    return {"intent": intent}
