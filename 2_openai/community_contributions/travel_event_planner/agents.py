from __future__ import annotations

from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field


# Structured outputs (planner + writer)


class DaySearch(BaseModel):
    """One web search slot inside a day: rationale plus the exact query string."""

    reason: str = Field(description="Why this search matters for that day.")
    query: str = Field(description="Web search query string.")


class DayPlan(BaseModel):
    """A single calendar day in the trip: narrative goals plus 2–3 targeted searches."""

    day_index: int = Field(description="1-based day number.")
    title: str = Field(description="Short label, e.g. 'Arrival & historic center'.")
    goals: str = Field(description="What the traveler should accomplish or experience this day.")
    searches: list[DaySearch] = Field(
        description="2-3 targeted searches for this day (areas, venues, events, logistics)."
    )


class TripPlan(BaseModel):
    """Full structured plan produced by the planner agent before any web search runs."""

    trip_title: str = Field(description="One-line title for the trip or event plan.")
    overview: str = Field(
        description="2-4 sentences: destination, vibe, constraints, season if inferred."
    )
    days: list[DayPlan] = Field(
        description="One entry per calendar day; each day has its own search bundle."
    )


class ItineraryReport(BaseModel):
    """Final artifact from the writer: narrative itinerary plus metadata for display or files."""

    short_summary: str = Field(description="2-3 sentence overview of the itinerary.")
    markdown_itinerary: str = Field(
        description="Full day-by-day itinerary in Markdown with times, areas, and concrete suggestions."
    )
    practical_tips: str = Field(
        description="Brief bullets: transport, money, bookings, etiquette, safety — grounded in research."
    )
    follow_up_questions: list[str] = Field(
        description="Optional deeper research topics or clarifications for the traveler."
    )


# System prompts

PLANNER_INSTRUCTIONS = """You are an expert travel and event planner assistant.
Given a natural-language trip or event request, produce a structured plan.

Rules:
- Infer destination, number of days, interests, budget level if mentioned, and season or dates if given.
- If the number of days is unclear, assume 3 days. If the user asks for a single-day event, output exactly one day.
- Each day must have its own title, goals, and 2-3 web search queries tailored to that day (neighborhoods,
  specific activities, venues, opening hours, seasonal events, transit between areas).
- Queries should be specific enough for web search (include city/region names, year or season when relevant).
- For conference or festival requests, include logistics searches (venue, schedule, nearby stays) on the right days.
- Output only the structured fields; no extra commentary outside the schema.
"""

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly; complete sentences optional. "
    "This will be consumed by someone writing a travel itinerary, so capture the essence and ignore fluff. "
    "Do not include any additional commentary other than the summary itself."
)

WRITER_INSTRUCTIONS = (
    "You are a senior travel editor. You receive the traveler's original request, a structured day plan "
    "(titles, goals), and raw web research summaries grouped by day.\n"
    "Produce a cohesive Markdown itinerary: for each day, use ### Day N — Title, then a realistic "
    "schedule with time blocks, neighborhoods, named places when supported by research, and transit notes. "
    "If research is thin, say what is unverified and suggest confirming hours or bookings.\n"
    "Keep practical_tips grounded in the summaries; do not invent specific prices or schedules not implied by research."
)


# Agent instances (gpt-4o-mini + hosted web search on researcher only)

planner_agent = Agent(
    name="TripPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=TripPlan,
)

search_agent = Agent(
    name="TripSearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

writer_agent = Agent(
    name="ItineraryWriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ItineraryReport,
)
