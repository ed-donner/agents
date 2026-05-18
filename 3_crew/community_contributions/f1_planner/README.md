# F1 Trip Planner

A multi-agent AI system built with [CrewAI](https://crewai.com) that plans a complete, budget-aware trip to any Formula 1 Grand Prix — flights, accommodation, race tickets, city itinerary, and a final executive briefing — all from a single set of inputs.

## What it does

Given a source city, destination Grand Prix, trip duration, and budget, the crew runs six specialist agents in sequence and produces six output files:

| Agent | Output file | What it produces |
|---|---|---|
| Travel Logistics | `flight_research.md` | Live flight options with prices and a Google Flights booking link |
| Travel Logistics | `accommodation.md` | Three hotel tiers (Trackside / Hub / Value Play) with nightly rates and booking links |
| F1 Experience Strategist | `race_ticket.md` | Grandstand recommendations with live ticket prices, circuit map insight, and budget assessment |
| Budget Planner | `budget_plan.md` | Accommodation tier selection, daily allowance, budget classification (CRITICAL / BUDGET / COMFORTABLE / LUXURY), and spending allocation |
| Local Guide | `local_guide.md` | Day-by-day city itinerary for all trip days, with costs targeting the daily allowance |
| Master Planner | `master_planner.md` | Full executive briefing — day-by-day table, total trip cost, risks, and booking priorities |

## Agents

- **Travel Logistics Agent** — Researches race weekend dates, calculates arrival/departure dates, searches live flights (via SerpApi Google Flights), and searches three hotel tiers (via SerpApi Google Hotels). Split into two tasks to keep each tool-call count low and prevent iteration exhaustion.
- **F1 Experience Strategist** — Searches official ticket categories and prices, fetches live exchange rates, recommends the best-value grandstand, and performs per-ticket budget assessment.
- **Budget Planner Agent** — Selects the hotel tier using a top-down trial (Trackside → Hub → Value Play) to keep fixed costs within 70% of the total budget, calculates the daily allowance, and classifies the trip (CRITICAL / BUDGET / COMFORTABLE / LUXURY).
- **Local Guide** — Plans a full day-by-day city itinerary that targets the daily allowance, distinguishing F1 session days from free days.
- **Master Planner** — Synthesizes all reports into a single executive briefing. Uses only data from upstream agents — never fabricates activities or costs.

All agents run on `openai/gpt-4o`. 
All tasks run sequentially. Each downstream task receives its upstream tasks as context.

## Tools

| Tool | Source | Purpose |
|---|---|---|
| `GoogleFlightsTool` | SerpApi Google Flights | Live flight prices, schedules, and booking URL |
| `GoogleHotelsPriceTool` | SerpApi Google Hotels | Live nightly rates, total costs, and booking links per tier |
| `CurrencyExchangeTool` | open.er-api.com (no key required) | Live exchange rates for ticket price conversion |
| `SerperDevTool` | Serper.dev | General web search for race dates, session times, attractions |

## Requirements

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/) (dependency manager)
- OpenAI API key
- SerpApi API key
- Serper API key

## Setup

**1. Install uv**

```bash
pip install uv
```

**2. Navigate to the project directory and install dependencies**

```bash
cd 3_crew/f1_planner
crewai install
```

**3. Create a `.env` file** in the project root with your API keys:

```
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
SERPER_API_KEY=...
```

## Configuration

Edit the inputs in `src/f1_planner/main.py` to plan your trip:

```python
inputs = {
    'source_city': 'Hyderabad',          # Your departure city
    'destination_city': 'Singapore',     # Grand Prix city
    'grand_prix': '2026 Singapore Grand Prix',
    'days': 6,                           # Total trip length in days
    'amount': '200000',                  # Total budget (as a string)
    'currency_code': 'INR',             # Your preferred currency
    'current_year': str(datetime.now().year)
}
```

The `amount` and `currency_code` are passed through all agents — the budget planner, ticket strategist, and local guide all work in the same currency end-to-end.

## Running

```bash
crewai run
```

Outputs are written to the `output/` directory as Markdown files. The final `master_planner.md` is the single document to share or act on.

## Project structure

```
f1_planner/
├── output/
│   ├── flight_research.md
│   ├── accommodation.md
│   ├── race_ticket.md
│   ├── budget_plan.md
│   ├── local_guide.md
│   └── master_planner.md
├── src/f1_planner/
│   ├── config/
│   │   ├── agents.yaml       # Agent roles, goals, backstories, LLM
│   │   └── tasks.yaml        # Task descriptions, expected outputs, context chains
│   ├── tools/
│   │   └── tools.py          # GoogleFlightsTool, GoogleHotelsPriceTool, CurrencyExchangeTool
│   ├── crew.py               # Crew assembly — agents, tasks, max_iter settings
│   └── main.py               # Entry point — trip inputs
└── pyproject.toml
```

## Key design decisions

- **Task splitting**: The original `travel_logistics_task` was split into `flight_research_task` and `accommodation_research_task` because a single task with 7+ tool calls frequently exhausted the agent's iteration budget. Smaller tasks (3–4 tool calls each) complete reliably.
- **Anti-batching instructions**: The local guide agent previously tried to batch multiple search queries into a single action, which CrewAI rejects. Explicit "call tools ONE AT A TIME" instructions prevent this.
- **Top-down budget trial**: The budget planner tries Trackside → Hub → Value Play in order and accepts the first tier where fixed costs stay within 70% of the total budget. This prevents negative daily allowances.
- **Live currency conversion**: The `CurrencyExchangeTool` uses `open.er-api.com` (no API key required) to get live exchange rates. The F1 Experience Strategist is explicitly instructed to use this tool by name rather than searching or guessing.
- **Master planner gating**: The master planner checks whether the local guide output contains "Estimated Day Cost" lines before synthesising the itinerary. If the local guide failed, it states so explicitly rather than fabricating activities.


## Disclaimer
This project is designed to provide a planning baseline for an F1 trip, not final travel advice. Prices, schedules, availability, and regulations can change quickly, so always verify all details with official booking providers and event organizers before making payments or travel decisions.