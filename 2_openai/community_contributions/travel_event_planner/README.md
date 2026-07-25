# Travel / event planner

Multi-agent trip planner built with the **OpenAI Agents SDK**: a structured day-by-day plan, **parallel web search** per query, and a Markdown itinerary printed or saved to a file.

## What it does

1. **Planner** — Turns a natural-language request into a `TripPlan` (each day has 2–3 targeted search queries).
2. **Search** — Runs those queries in parallel via `WebSearchTool` (OpenAI-hosted; billed separately from chat tokens).
3. **Writer** — Merges research into an `ItineraryReport` (summary, Markdown itinerary, practical tips, follow-up ideas).

## Requirements

- `openai-agents` / `agents`
- `openai`
- `pydantic`
- `python-dotenv`

## Environment variables

| Variable           | Required | Purpose                                     |
| ------------------ | -------- | ------------------------------------------- |
| `OPENAI_API_KEY`   | Yes      | Chat + structured outputs + web search tool |

Optional: load from a `.env` file in the working directory (`load_dotenv` in `main.py`).

## How to run

From `2_openai/community_contributions` (with the project virtualenv active or `uv run` from the repo):

```bash
python -m travel_event_planner.main "3 days in Lisbon, food and tiles, March 2026"
python -m travel_event_planner.main "Weekend in Chicago, architecture" -o trip.md
```

### CLI options

- `-o FILE` / `--out` — Write the full Markdown report to a file.

## Programmatic use

```python
import asyncio
from travel_event_planner.main import run_trip, build_report_document

async def demo():
    report = await run_trip("2 days in Porto, wine and riverfront")
    print(build_report_document(report))

asyncio.run(demo())
```

## Cost notes

- Chat usage uses `gpt-4o-mini` (see OpenAI pricing).
- **`WebSearchTool`** incurs additional per-call web search fees; parallel searches multiply calls.
