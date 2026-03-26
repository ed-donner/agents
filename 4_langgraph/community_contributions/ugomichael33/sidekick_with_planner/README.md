# Sidekick With Planner (Week 4)

This project is a LangGraph-based Sidekick agent with a planning step and evaluator loop. It uses tools for search, Wikipedia, Python REPL, and file management. Optional browser automation is available via Playwright.

## Features
- Planner node that builds a short plan before execution
- Tool-using worker node with LangGraph tool routing
- Evaluator loop to enforce success criteria
- Memory checkpointing
- Gradio UI for interactive testing

## Setup
Create a `.env` file in this folder with:
```
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
MODEL=openai/gpt-4o-mini

PUSHOVER_TOKEN=...      # optional
PUSHOVER_USER=...       # optional
ENABLE_BROWSER=false    # set true to enable Playwright browser tools
```

Install dependencies:
```
uv pip install -r requirements.txt
```

Run the app:
```
uv run python app.py
```

## Notes
- The file tools are scoped to the local `sandbox/` directory.
- If you enable the browser tools, make sure Playwright has its browsers installed.
