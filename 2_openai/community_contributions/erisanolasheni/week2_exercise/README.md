# Week 2 community contribution — Erisan Olasheni

Extends the course **deep research** pattern with:

1. **Clarifying questions** — An agent proposes three scope questions; the user answers in the UI before the main run (same idea as OpenAI’s deep-research scoping).
2. **Agentic expansion** — After the first search batch, an **expansion agent** decides whether up to three follow-up web searches are needed (capped), using the brief plus current summaries.
3. **Evaluator → optional revision** — An **evaluator agent** checks the draft; if it is not adequate, one **writer** revision pass is triggered with concrete feedback.
4. **Streaming status** — The manager `yield`s progress strings for Gradio (same pattern as the instructor’s `research_manager` + generator callback).

## Run

From this directory (with the repo’s virtualenv or `uv`):

```bash
cd 2_openai/community_contributions/erisanolasheni/week2_exercise
uv run python app.py
```

Ensure a project `.env` (or cwd `.env`) includes:

- `OPENAI_API_KEY` **or** `OPENROUTER_API_KEY` (with `OPENAI_BASE_URL` / `OPENAI_API_BASE` when using a proxy).

Optional email (otherwise the email step still runs but may no-op):

- `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `SENDGRID_TO_EMAIL`

To skip email entirely:

- `SKIP_EMAIL=1`

## Files

| File | Role |
|------|------|
| `config.py` | `RunConfig` + `OpenAIProvider` for custom base URL / key |
| `schemas.py` | Shared Pydantic outputs |
| `clarify_agent.py` | Three clarifying questions |
| `planner_agent.py` | Initial `WebSearchPlan` (3 queries) |
| `expansion_agent.py` | Optional follow-up searches (≤3) |
| `search_agent.py` | `WebSearchTool` with `search_context_size="low"` |
| `writer_agent.py` | `ReportData` markdown report |
| `evaluator_agent.py` | Adequacy + revision brief |
| `email_agent.py` | SendGrid tool (env-driven addresses) |
| `research_manager.py` | Async generator orchestration |
| `app.py` | Gradio Blocks UI |
| `week2_exercise.ipynb` | Short narrative for the assignment |

## Git / PR workflow

- Branch: `week2` (from upstream `main` when possible).
- Remote: `myfork` → `git@github.com:erisanolasheni/agents.git`
- Open a PR from `myfork:week2` (or your fork branch) to **ed-donner/agents** `main`.

## Hugging Face (optional)

Same as week 1: from this folder, `uv run gradio deploy` and set Space secrets for your API keys (and SendGrid if used).
