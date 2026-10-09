"""Tasks agent node: project tracking, priorities, and status updates."""

from langchain_core.messages import HumanMessage, AIMessage
from llm_client import get_llm
from agents.state import AgentState

TASKS_SYSTEM = """You are SideKick, a professional AI assistant for a Senior Project Manager at a software development company.

Your project & task management capabilities:
- Help structure and prioritize tasks and project deliverables
- Draft status update reports for the CEO/Managing Partner
- Identify risks, blockers, and dependencies in project descriptions
- Suggest action items and owners based on project context
- Format outputs as clear, executive-ready summaries

Use structured formats where helpful:
- Priority lists: 🔴 Critical | 🟡 Important | 🟢 Nice-to-have
- Status reports: Project | Status | Owner | Next Step | Due Date
- Risk flags: ⚠️ Risk | Impact | Mitigation

Always be direct, specific, and actionable. Avoid filler language.
"""


def tasks_node(state: AgentState) -> dict:
    """Handles task/project tracking intent."""
    llm = get_llm(temperature=0.3)
    last_human = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
    )

    # Include prior conversation turns as context (last 6 messages)
    history = ""
    prior = [m for m in state.messages if not isinstance(m, HumanMessage)][-6:]
    if prior:
        history = "\nPrevious context:\n" + "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in prior
        )

    user_message = last_human.content if last_human else ""
    full_prompt = f"{TASKS_SYSTEM}{history}\n\nUser request: {user_message}"

    response = llm.invoke(full_prompt)
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }
