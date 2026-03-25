# Government policy deep research (OpenAI Agents SDK)

Multi-agent flow modeled on the course [`deep_research/`](https://github.com/ed-donner/agents/tree/main/2_openai/deep_research) pattern: **planner → parallel web search → structured policy brief**. Email is omitted so you only need `OPENAI_API_KEY` (no SendGrid).

**Target upstream for PRs:** [github.com/ed-donner/agents](https://github.com/ed-donner/agents) — add only this folder under `2_openai/community_contributions/`.

## Setup

- Use the repo’s existing virtualenv and dependencies (`agents`, `openai`, `gradio`, `python-dotenv` from the main course `requirements` / `uv` setup).
- Export secrets locally (do not commit):

```bash
export OPENAI_API_KEY="sk-..."
```

Or rely on a `.env` at the **repo root** (not committed); `run.py` and `app.py` call `load_dotenv()`.

## Run (Gradio)

```bash
cd 2_openai/community_contributions/abdussamadbello_policy_deep_research
python app.py
```

Opens a browser tab with a text box, streaming status lines, then the markdown brief.

## Run (CLI)

```bash
python run.py "Compare EU and US approaches to digital markets regulation at a high level"
```

Default query runs if you pass no arguments (US EPA GHG reporting theme).

## Cost note

Uses `WebSearchTool` and multiple model calls; monitor usage on the OpenAI dashboard.

## Disclaimer

Output is **research draft only**, not legal advice. Verify all claims against official instruments and qualified professionals.

## Files

| File | Role |
|------|------|
| `policy_agents.py` | Planner, search, and writer agents + Pydantic output types |
| `research_manager.py` | Async orchestration and tracing |
| `run.py` | CLI |
| `app.py` | Gradio UI |
| `README.md` | This file |


