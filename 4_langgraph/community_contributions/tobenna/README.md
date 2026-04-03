# Job agency (LangGraph + Gradio)

**Inginia’s Job Agency** is a small Gradio app backed by a LangGraph workflow: you paste a CV, the graph reviews it, uses a **Playwright** browser to search for jobs, scores how well listings match, then shows a markdown summary. Results are also written under `output/` as timestamped `.md` and `.json`. Optional **Pushover** notification is supported if you configure it in `.env`.

## Run

From the repo root (with the course `uv` environment), or from this folder if your dependencies are already available:

```bash
cd 4_langgraph/community_contributions/tobenna
uv run app.py
```

Set `OPENAI_API_KEY` (e.g. in `.env`); Playwright will open a Chromium window for the search step.
