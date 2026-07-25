# Lead Intake AI

## Requirements

You need:

- the repo Python environment set up
- `OPENAI_API_KEY` available in your environment or `.env`
- optional `PUSHOVER_USER` and `PUSHOVER_TOKEN` values for live push notifications

## Run

From the repo root:

```bash
cd 6_mcp/community_contributions/tobenna
uv run app.py
```

## How to Use

1. Paste an inbound email, note, or website inquiry into `Lead brief`.
2. Optionally fill in structured fields.
3. Click `Process lead`.
4. Review the staged workflow summary for intake, qualification, routing, and notification.
5. Review the refreshed leads table for qualification, routing, and notification state.
