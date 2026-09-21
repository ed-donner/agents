"""General agent node: handles open-ended queries and fallback conversations."""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from llm_client import get_llm
from agents.state import AgentState

GENERAL_SYSTEM = """You are SideKick, a sharp and professional AI assistant for a Senior Project Manager at a software development solutions company.

You work alongside a PM who:
- Reports directly to the CEO/Managing Partner
- Works with both technical and non-technical professionals daily
- Builds and promotes software solutions to clients
- Operates in a high-stakes, fast-paced environment

Be concise, direct, and professional. Offer practical, experienced-level insights.
Avoid filler, fluff, and over-explanation. When relevant, offer structured outputs.
"""


def general_node(state: AgentState) -> dict:
    """Handles general queries with full conversation history for context."""
    llm = get_llm(temperature=0.5)

    # Include conversation history (last 10 messages) for multi-turn continuity
    history = state.messages[-10:]
    messages = [SystemMessage(content=GENERAL_SYSTEM)] + history

    response = llm.invoke(messages)
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }
