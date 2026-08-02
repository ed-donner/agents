# Incident Postmortem Crew

A small [CrewAI](https://crewai.com) project that drafts a **blameless** incident postmortem from raw notes: timeline, impact, root-cause analysis, and actionable follow-ups. Use the [CrewAI docs](https://docs.crewai.com) for framework details.

## Problem it solves

After outages or serious bugs, teams need a **consistent, blameless postmortem**: timeline, impact, root cause, contributing factors, and concrete follow-ups. Doing this well is repetitive and easy to skip under pressure. A small CrewAI project automates the **structure and first draft** so humans only review and approve.

## What it does

Three agents run in sequence:

1. **Incident summarizer** — Builds a neutral timeline and impact summary.
2. **Root cause analyst** — Blameless RCA (proximate vs systemic factors, contributing factors, what went well).
3. **Action owner** — Merges everything into a single Markdown file with fixed headings and SMART-style action items.

## Disclaimer

This produces a **draft** for human review. Do not treat LLM output as authoritative for compliance, customer communications, or liability. Always verify facts, dates, and owners before publishing.

## Installation

Requires Python `>=3.10,<3.14` and [uv](https://docs.astral.sh/uv/).

```bash
cd 3_crew/community_contributions/incident_postmortem
uv sync
```

## Configuration

Copy `.env.example` to `.env` and set:

- `OPENAI_API_KEY` — required for the default OpenAI models referenced in `agents.yaml`.

To use another provider or model, edit `src/incident_postmortem/config/agents.yaml` (`llm` fields per [CrewAI agent configuration](https://docs.crewai.com/concepts/agents)).

## Running

From this project directory:

```bash
uv run crewai run
```

Or:

```bash
uv run python -m incident_postmortem.main
```

Outputs:

- `output/postmortem.md` — final postmortem (from the last task’s `output_file` in `tasks.yaml`). The file in the repo is an example produced from the sample notes in `main.py`; your run will overwrite it.

## Customizing inputs

Edit `src/incident_postmortem/main.py`:

- `INCIDENT_NOTES` — paste chat logs, pager text, or bullet notes.
- `service_name`, `severity` — strings passed into the YAML task templates.
- `report_date` — defaults to today; override if you want a fixed date.

## Project layout

| Path | Purpose |
|------|---------|
| `src/incident_postmortem/config/agents.yaml` | Agent roles and goals |
| `src/incident_postmortem/config/tasks.yaml` | Task descriptions and `output/postmortem.md` |
| `src/incident_postmortem/crew.py` | Crew wiring |
| `src/incident_postmortem/main.py` | Entrypoint and sample incident |
| `knowledge/user_preference.txt` | Blameless tone hints (optional knowledge expansion) |

## Support

- [CrewAI documentation](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/crewAIInc/crewAI)
