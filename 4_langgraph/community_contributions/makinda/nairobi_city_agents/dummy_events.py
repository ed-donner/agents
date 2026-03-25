"""LLM-generated synthetic Nairobi events when the local DB is empty (dummy-data agent)."""

from datetime import date, timedelta

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from config import CITY, LLM_MODEL
from local_db import insert_event


class SyntheticEvent(BaseModel):
    event_name: str = Field(description="Name of the event")
    event_date: str = Field(
        description="Date between today and ~4 months out; must use the current calendar year"
    )
    description: str = Field(description="One or two sentences")
    venue: str = Field(description="Neighborhood or venue in Nairobi")


class SyntheticEventBatch(BaseModel):
    events: list[SyntheticEvent] = Field(
        min_length=3,
        max_length=6,
        description="Plausible community and cultural events in Nairobi",
    )


def run_dummy_data_agent() -> int:
    """Ask the LLM for plausible dummy events and persist them. Returns rows inserted."""
    today = date.today()
    horizon = today + timedelta(days=120)
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7)
    structured = llm.with_structured_output(SyntheticEventBatch)
    prompt = f"""
You are generating **synthetic but realistic** upcoming events for {CITY}, Kenya
for a demo database. Include a mix of: music/culture, tech meetups,
community / climate awareness, and outdoor markets.

**Critical — dates:** Today is **{today.isoformat()}** ({today.strftime("%A")}). Every `event_date`
must fall between **{today.isoformat()}** and **{horizon.isoformat()}** inclusive, and must use
the **{today.year}** calendar year (not {today.year - 1} or earlier). Prefer explicit calendar
dates (e.g. "2026-04-12" or "12 April {today.year}").

Venues: real Nairobi neighborhoods (Westlands, Kilimani, Karen, CBD) or plausible hall names.
Do not claim these are officially verified — placeholders for local DB seeding only.
"""
    batch: SyntheticEventBatch = structured.invoke(prompt)
    for ev in batch.events:
        insert_event(
            CITY,
            ev.event_name,
            ev.event_date,
            ev.description,
            ev.venue,
        )
    return len(batch.events)
