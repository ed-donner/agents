"""Tool fetcher node: loads live data from Gmail/Calendar/Tavily before agent nodes run."""

import logging
from langchain_core.messages import HumanMessage
from agents.state import AgentState

logger = logging.getLogger(__name__)


def tool_fetcher_node(state: AgentState) -> dict:
    """
    Pre-fetch external data based on intent.
    Populates state.tool_data so downstream agents have live context.
    Failures are caught and logged — the agent degrades gracefully.
    """
    intent = state.intent
    tool_data: dict = {}

    if intent == "email":
        tool_data = _fetch_emails()

    elif intent == "calendar":
        tool_data = _fetch_events()

    elif intent == "research":
        last_human = next(
            (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
        )
        query = last_human.content if last_human else ""
        tool_data = _fetch_search(query)

    return {"tool_data": tool_data}


def _fetch_emails() -> dict:
    try:
        from tools.gmail_tool import get_recent_emails
        return {"emails": get_recent_emails(max_results=10)}
    except Exception as e:
        logger.warning("Gmail fetch failed: %s", e)
        return {"emails": [], "error": str(e)}


def _fetch_events() -> dict:
    try:
        from tools.calendar_tool import get_upcoming_events
        return {"events": get_upcoming_events(max_results=10)}
    except Exception as e:
        logger.warning("Calendar fetch failed: %s", e)
        return {"events": [], "error": str(e)}


def _fetch_search(query: str) -> dict:
    try:
        from tools.research_tool import web_search
        return {"search_results": web_search(query, max_results=5)}
    except Exception as e:
        logger.warning("Search fetch failed: %s", e)
        return {"search_results": [], "error": str(e)}
