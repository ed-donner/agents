# Week 3 assessment — CrewAI multi-agent crew

Submission for **Week 3 (CrewAI)** of the agents course: a **sequential crew** of three agents that produces a **payments / financial inclusion** strategy brief (research → risk review → executive synthesis).

## What it demonstrates

| Course theme | This repo |
|--------------|-----------|
| Multiple agents with distinct roles | Research analyst, risk specialist, synthesizer |
| Task handoff via `context=` | Later tasks consume earlier task outputs |
| `crewai run`–style workflow | Runnable script + `uv` env in this folder |

## Setup

From **this directory**:

```bash
cd 3_crew/community_contributions/idumachika_week3
uv sync
```

Put **`OPENAI_API_KEY`** in the **repository root** `agents/.env` (same as the rest of the course).

- **OpenRouter** keys (`sk-or-...`): the script sets `OPENAI_API_BASE` to OpenRouter automatically.
- **OpenAI.com**: use `sk-proj-...` and do not set a custom base URL unless you use a gateway.

Optional: custom topic (otherwise a default inclusion topic is used):

```bash
uv run python payment_inclusion_crew.py "Your topic in quotes"
# or
export CREW_TOPIC="Your topic"
uv run python payment_inclusion_crew.py
```

## Output

- Markdown report: **`output/week3_payment_inclusion_brief.md`** (folder is gitignored).

## PR

Add this folder under `3_crew/community_contributions/` and open a PR to [ed-donner/agents](https://github.com/ed-donner/agents) from your fork.
