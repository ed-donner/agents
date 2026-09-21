# Job Hunt Assistant 

A **LangGraph** portfolio project for the Week 4 track: research job postings, summarize JDs, align keywords, and draft outreach — with **tools** (including optional **Pushover** notifications), **SQLite checkpointing**, optional **Playwright** browser tools, and a **structured-output evaluator** that can send the worker back for another pass.


## Setup

1. Install [uv](https://docs.astral.sh/uv/) if you do not have it yet.

2. Create a virtual environment and install dependencies:

   ```bash
   cd 4_langgraph/community_contributions/adams-bolaji
   uv venv
   uv pip install -r requirements.txt
   ```

   If you already use the repo root `.venv`, you can instead run  
   `uv pip install -r requirements.txt` from that environment (or point `uv pip` at `-p path/to/python`).

3. Copy `.env.example` to `.env` and set at least `OPENAI_API_KEY`.

4. **Web search:** `search_web` works **without Serper** using DuckDuckGo via the **`ddgs`** package (in `requirements.txt` — no signup). Optionally set `SERPER_API_KEY` for Google-style results through [Serper](https://serper.dev/). You can always combine with `wikipedia_lookup` and `fetch_job_page_text` for URLs you paste.

   Optional: **Pushover** — set `PUSHOVER_TOKEN` and `PUSHOVER_USER` in `.env` so the assistant can call `send_push_notification` when you ask for a ping (e.g. when a draft is ready). See [pushover.net](https://pushover.net/).

5. Optional: Playwright browsers (for Lab 3-style tools):

   ```bash
   uv run python -m playwright install chromium
   ```

   To skip browser tools (CI or quick dev): set `JOB_HUNT_DISABLE_BROWSER=1` in `.env`.

6. Run the UI:

   ```bash
   uv run python app.py
   ```

Artifacts are written under `sandbox/applications/`. Checkpoint DB: `sandbox/job_hunt_checkpoints.db` (gitignored).

## Usage tips

- Fill **Profile / targets** once (role, stack, location), then iterate in **What do you want this turn?**
- **Success criteria** drives the evaluator (e.g. “Must save `company_role.md` and list 5 JD keywords with quotes”).
- Ask for a **Pushover ping** in your request or criteria (e.g. “Notify me when the draft is saved”) if `PUSHOVER_*` is set in `.env`.
- Each **New session** creates a fresh assistant and a new checkpoint thread id.

## Files

- `job_hunt_assistant.py` — graph, worker, evaluator, SQLite checkpointer
- `job_hunt_tools.py` — search, Wikipedia, HTTP fetch, save/list/read application packages, Pushover, Playwright
- `app.py` — Gradio interface
