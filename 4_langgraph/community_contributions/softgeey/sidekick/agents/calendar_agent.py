"""Calendar agent node: meeting prep, summaries, and scheduling advice."""

from langchain_core.messages import HumanMessage, AIMessage
from llm_client import get_llm
from agents.state import AgentState

CALENDAR_SYSTEM = """You are SideKick, a professional AI assistant for a Senior Project Manager at a software development company.

Your calendar tasks:
- Summarize upcoming meetings clearly
- Prepare briefing notes for specific meetings (attendees, agenda, talking points)
- Identify scheduling conflicts or back-to-back pressure points
- Suggest preparation steps for client or executive meetings
- Keep responses concise, structured, and actionable

Format meeting summaries as:
📅 [Date & Time] — [Meeting Title]
👥 Attendees: [list]
📍 Location/Link: [if available]
📝 Notes: [agenda or description]
"""


def calendar_node(state: AgentState) -> dict:
    """Handles calendar/meeting intent with fetched event data as context."""
    llm = get_llm(temperature=0.3)
    last_human = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
    )

    # Build context from fetched events if available
    event_context = ""
    events = state.tool_data.get("events", [])
    if events:
        lines = ["Upcoming calendar events:\n"]
        for i, e in enumerate(events[:8], 1):
            attendees = ", ".join(e["attendees"][:5]) if e["attendees"] else "N/A"
            lines.append(
                f"{i}. {e['summary']}\n"
                f"   Start: {e['start']} | End: {e['end']}\n"
                f"   Location: {e['location'] or 'N/A'}\n"
                f"   Attendees: {attendees}\n"
                f"   Notes: {e['description'] or 'None'}\n"
            )
        event_context = "\n".join(lines)

    user_message = last_human.content if last_human else ""
    full_prompt = f"{CALENDAR_SYSTEM}\n\n{event_context}\n\nUser request: {user_message}"

    response = llm.invoke(full_prompt)
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }
