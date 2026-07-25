# Week 2 assessment — Deep research + structured email

This submission extends **`2_openai/4_lab4.ipynb`** (deep research) and touches **`3_lab3.ipynb`** ideas (structured outputs for email).

## What it does

| Piece | Notes |
|--------|--------|
| **Clarification agent** | Before planning searches, asks 2–4 structured questions and merges answers into the research brief (`CLARIFY_ANSWERS` or placeholders if omitted). |
| **Planner + parallel search** | Same pattern as Lab 4: `WebSearchPlan` → parallel `WebSearchTool` calls. |
| **Writer** | `ReportData` with summary, markdown report, follow-ups. |
| **Structured email** | `EmailDraft` (subject + HTML body) via a dedicated formatter agent; SendGrid sends if configured. |
| **Artifact** | Always writes `week2_report_output.md` next to this script. |

## Run

From the **repository root** (with `uv` / `.venv` and `OPENAI_API_KEY` in `.env`):

```bash
uv run python 2_openai/community_contributions/idumachika_week2/week2_deep_research.py \
  "Topic for your research" --skip-clarification
```

Use `--skip-clarification` for quick runs or when you do not want extra clarification questions.

**Full flow** (clarification on): omit `--skip-clarification` and optionally set answers:

```bash
export CLARIFY_ANSWERS=$'Focus on open source.\n---\nEurope and US only.'
uv run python 2_openai/community_contributions/idumachika_week2/week2_deep_research.py \
  "AI agent frameworks in 2026"
```

**Email (optional):** set `SENDGRID_API_KEY`, and verified sender/recipient `SENDGRID_FROM_EMAIL` / `SENDGRID_TO_EMAIL`.

**Cost:** `WebSearchTool` is billed per use; see [OpenAI pricing](https://platform.openai.com/docs/pricing#web-search).

## PR

Submit this folder under `community_contributions` from your fork of [ed-donner/agents](https://github.com/ed-donner/agents).
