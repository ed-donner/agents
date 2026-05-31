# Week 5 AutoGen AgentChat Team — Email Draft

This project demonstrates AutoGen AgentChat with:
- A multi-agent team (RoundRobinGroupChat)
- Structured output via a Pydantic schema
- Local tools via FunctionTool

## How It Works
- **Researcher** pulls a style guide using a tool.
- **Writer** produces a structured JSON draft (schema-enforced).
- **Reviewer** gives feedback and ends with `APPROVE` when the draft meets criteria.

## Setup
Create a `.env` file in this folder:
```
OPENAI_API_KEY=sk-...
# Optional for OpenRouter:
# OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL=gpt-4o-mini
# If using OpenRouter, set:
# MODEL=openai/gpt-4o-mini
```

Install dependencies:
```
uv pip install -r requirements.txt
```

Run:
```
uv run python main.py
```

You should see the full conversation and a parsed JSON draft printed at the end.
