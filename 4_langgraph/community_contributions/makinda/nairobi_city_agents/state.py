"""Shared graph state (TypedDict + reducers pattern from LangGraph labs)."""

from typing import TypedDict


class NairobiCityState(TypedDict, total=False):
    """State flowing through the Nairobi city information workflow."""

    city: str
    user_question: str
    events_local: str
    events_online: str
    events_combined: str
    weather_info: str
    outfit_and_activities: str
    venues_rag_context: str
    final_briefing: str
