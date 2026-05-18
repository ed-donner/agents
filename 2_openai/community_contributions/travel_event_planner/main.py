from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

from agents import Runner
from dotenv import load_dotenv

from .agents import (
    DaySearch,
    ItineraryReport,
    TripPlan,
    planner_agent,
    search_agent,
    writer_agent,
)



# Per-search context (ties a query back to its day for the writer)


@dataclass(frozen=True)
class SearchContext:
    """Binds one planned search to its day so summaries can be grouped for the writer."""

    day_index: int
    day_title: str
    item: DaySearch


async def plan_trip(user_request: str) -> TripPlan:
    """Run the planner once; returns structured days and search queries (no web calls yet)."""
    result = await Runner.run(planner_agent, f"Trip or event request:\n{user_request}")
    return result.final_output


def _collect_search_contexts(trip: TripPlan) -> list[SearchContext]:
    """Flatten day plans into an ordered list of search jobs (sorted by day_index)."""
    contexts: list[SearchContext] = []
    ordered_days = sorted(trip.days, key=lambda d: d.day_index)
    for day in ordered_days:
        for item in day.searches:
            contexts.append(
                SearchContext(day_index=day.day_index, day_title=day.title, item=item)
            )
    return contexts


async def _run_one_search(ctx: SearchContext) -> tuple[SearchContext, str]:
    """Execute a single web-backed search and return the same context with the summary text."""
    payload = (
        f"Search term: {ctx.item.query}\n"
        f"Reason: {ctx.item.reason}\n"
        f"Day {ctx.day_index}: {ctx.day_title}"
    )
    result = await Runner.run(search_agent, payload)
    return ctx, result.final_output


async def perform_searches(trip: TripPlan) -> list[tuple[SearchContext, str]]:
    """Run all planned searches concurrently; preserves pairing via returned tuples."""
    contexts = _collect_search_contexts(trip)
    if not contexts:
        return []
    tasks = [asyncio.create_task(_run_one_search(c)) for c in contexts]
    return list(await asyncio.gather(*tasks))


def _format_research_for_writer(
    user_request: str, trip: TripPlan, results: list[tuple[SearchContext, str]]
) -> str:
    """Build one long prompt for the writer: request, overview, then per-day bullet summaries."""
    lines: list[str] = [
        f"Original request:\n{user_request}\n",
        f"Plan overview: {trip.trip_title}\n{trip.overview}\n",
        "--- Research by day ---\n",
    ]
    by_day: dict[int, list[tuple[SearchContext, str]]] = {}
    for ctx, text in results:
        by_day.setdefault(ctx.day_index, []).append((ctx, text))
    for day in sorted(trip.days, key=lambda d: d.day_index):
        lines.append(f"\n## Day {day.day_index}: {day.title}\nGoals: {day.goals}\n")
        for ctx, text in by_day.get(day.day_index, []):
            lines.append(f"- Query: {ctx.item.query}\n  Summary:\n{text}\n")
    return "\n".join(lines)


async def write_itinerary(
    user_request: str, trip: TripPlan, results: list[tuple[SearchContext, str]]
) -> ItineraryReport:
    """Synthesize search results into a structured Markdown itinerary + tips + follow-ups."""
    body = _format_research_for_writer(user_request, trip, results)
    result = await Runner.run(writer_agent, body)
    return result.final_output


async def run_trip(user_request: str) -> ItineraryReport:
    """End-to-end: plan → parallel search → write."""
    trip = await plan_trip(user_request)
    search_pairs = await perform_searches(trip)
    return await write_itinerary(user_request, trip, search_pairs)


def build_report_document(report: ItineraryReport) -> str:
    """Single Markdown document for stdout, files, or pipes (summary + itinerary + tips + questions)."""
    return "\n\n".join(
        [
            "## Summary",
            report.short_summary,
            "## Itinerary",
            report.markdown_itinerary,
            "## Practical tips",
            report.practical_tips,
            "## Follow-up ideas",
            "\n".join(f"- {q}" for q in report.follow_up_questions),
        ]
    )



# CLI


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="travel_event_planner.main",
        description=(
            "Plan a trip or event using OpenAI Agents: structured multi-day plan, "
            "parallel web search per query, then a Markdown itinerary. "
            "Requires OPENAI_API_KEY; web search may incur extra charges."
        ),
    )
    parser.add_argument(
        "request",
        nargs="?",
        help='Natural language trip/event description, e.g. "3 days in Lisbon, food and tiles, March 2026"',
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        metavar="FILE",
        help="Write the full Markdown report to this path.",
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> None:
    load_dotenv(override=True)
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if not args.request or not args.request.strip():
        print(
            "Usage: provide a trip request string (see --help). "
            "Example: python -m travel_event_planner.main \"2 days in Porto\"",
            file=sys.stderr,
        )
        sys.exit(2)

    req = args.request.strip()
    print("Planning and searching (web calls may incur OpenAI web search fees)...", file=sys.stderr)
    report = await run_trip(req)

    doc = build_report_document(report)
    print()
    print(doc)

    if args.out:
        args.out.write_text(doc, encoding="utf-8")
        print(f"\nWrote {args.out.resolve()}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
