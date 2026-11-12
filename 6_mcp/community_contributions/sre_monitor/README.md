# SRE Monitor

SRE Monitor is an agentic incident-intelligence product built with LangGraph. It watches SaaS status pages,
detects newly reported or escalating incidents, evaluates severity and global impact, and sends actionable
alerts containing a concise summary and the original incident link.

It also produces a daily Markdown review of incidents and available postmortems from the previous 24 hours,
while a read-only web dashboard provides a live operational view.

Created by [Arunendu Roy](https://www.linkedin.com/in/arunenduroy/).

## Product capabilities

- Continuously polls multiple SaaS status pages without using an LLM for routine checks.
- Detects new incidents and severity escalations while preventing duplicate alerts.
- Classifies incidents as SEV1–SEV4 and identifies possible global impact.
- Independently corroborates SEV1/SEV2 impact using recent Reddit and web results from Serper.
- Sends formatted HTML email alerts with summaries, affected components, evidence and source links.
- Sends Pushover notifications for SEV1 and SEV2; SEV1 uses high priority.
- Generates and emails a daily Markdown incident/postmortem report.
- Stores operational state, activity and notification history in SQLite.
- Exposes a live dashboard and read-only JSON API.
- Sends LangGraph, model and tool traces to LangSmith.

The default configuration monitors GitHub, Cloudflare, Zscaler, OpenAI and Zoom. Services can be added or
removed in `config.yaml`.

## Agent workflow

Every specialist returns control to the Orchestrator through a LangGraph `Command`. Guardrails ensure that
required stages cannot be skipped.

1. **Orchestrator** selects the next required specialist.
2. **Status Watcher** confirms whether a status-page entry represents a customer-impacting incident.
3. **Triage** assigns severity, priority and preliminary global-impact status.
4. **Impact Verifier** runs for SEV1/SEV2 incidents and judges independent Serper evidence. Reddit alone is
   never treated as proof of global impact.
5. **Notifier** sends routine or priority email and push notifications.
6. **Postmortem Analyst** handles the separate daily review workflow and writes
   `reports/postmortem-<date>.md`.

The selected model is shared by every agent in a run. Models are called only when an incident is new,
escalated, or undergoing the scheduled daily review.

## Project layout

- `backend/engine.py` — polling scheduler and command-line entry point.
- `backend/agents.py` — LangGraph agents, handoffs and workflow guardrails.
- `backend/sources.py` — Statuspage, RSS and Zscaler data collection.
- `backend/serper.py` — independent outage-evidence search.
- `backend/emailer.py` — SMTP email and Pushover delivery.
- `backend/api.py` and `backend/dashboard.html` — dashboard and read-only API.
- `backend/store.py` — SQLite persistence in `data/monitor.db`.
- `backend/prompts.py` — all agent prompts.
- `config.yaml` — services, model, schedule, verification, tracing and recipients.

## Configuration

Run `uv sync` from the repository root, then create or update the repository-level `.env`:

```dotenv
# Choose the key required by llm.provider in config.yaml
OPENAI_API_KEY=...
GOOGLE_API_KEY=...

# Independent evidence search for SEV1/SEV2
SERPER_API_KEY=...

# SMTP email delivery (Gmail requires a 16-character app password)
EMAIL_ADDRESS=you@example.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_APP_PASSWORD=...

# Optional SEV1/SEV2 push notifications
PUSHOVER_USER=...
PUSHOVER_TOKEN=...

# Optional LangSmith tracing
LANGSMITH_API_KEY=...
```

Do not commit `.env`; it is ignored by Git.

Edit `config.yaml` to control:

- `llm.provider`: `openai` or `gemini`. Override one run with `SRE_LLM_PROVIDER=openai`.
- `monitor.poll_interval_minutes`: status-page polling frequency.
- `monitor.daily_review_hour`: local hour for the daily review.
- `verification.severities`: severities requiring independent verification.
- `email.recipients` and `email.priority_recipients`: alert destinations.
- `services`: monitored status pages and source adapters.
- `tracing.enabled` and `tracing.project`: LangSmith tracing.

Statuspage services use their JSON API, with RSS as a fallback. Zscaler uses its Trust Portal incident API.
Each SEV1/SEV2 verification consumes two Serper searches; lower severities consume none.

## Run

From `6_mcp/community_contributions/sre_monitor`, start the engine and dashboard in separate terminals:

```bash
uv run -m backend.engine
uv run uvicorn backend.api:app --port 8100
```

Open http://localhost:8100 to view current service health, active and recent incidents, agent activity,
notification history and generated reports.

Useful one-off commands:

```bash
uv run -m backend.engine --once
uv run -m backend.engine --daily-now
uv run -m backend.engine --once --dry-run
```

`--dry-run` writes email and push previews to `data/outbox` instead of sending them.

## Runtime behavior

A healthy poll with no changes is intentionally silent. Agent logs and LangSmith traces appear only when a
new/escalated incident triggers the workflow, when a source fails, or when the daily review runs. The dashboard's
last-poll timestamp confirms that background monitoring is active.

Generated runtime data is kept out of Git:

- `data/monitor.db` — service, incident, activity and notification state.
- `data/outbox/` — dry-run previews.
- `reports/` — daily Markdown reviews.
