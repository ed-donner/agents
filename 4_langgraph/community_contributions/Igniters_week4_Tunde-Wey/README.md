# Igniters Week 4 — Tunde Wey (Sidekick)

This folder is a self-contained copy of the Week 4 LangGraph **Sidekick** Gradio app (`4_langgraph/app.py`, `sidekick.py`, `sidekick_tools.py`) with **one** feature upgrade.

## Feature upgrade: configurable graph recursion limit

Each user message runs the Sidekick graph (worker → tools → evaluator loop). LangGraph can run many steps before finishing. This version passes a **`recursion_limit`** into `graph.ainvoke` so long or stuck runs stop deterministically instead of burning tokens indefinitely.

- **Environment variable:** `SIDEKICK_RECURSION_LIMIT` (integer).
- **Default:** `50` if unset or invalid.
- **Clamp:** values are clamped to `1`–`500` so typos do not explode the run.

Implementation: `sidekick.py` — `sidekick_recursion_limit()` and the `config` dict in `run_superstep`.

## Run

From this directory (after `pip install -r requirements.txt` and `playwright install chromium`):

```bash
copy .env.example .env
# Edit .env with your keys, then:
python app.py
```

Ensure a `sandbox/` folder exists for file tools (included via `.gitkeep`).
