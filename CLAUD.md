# CLAUD.md

Guidance for Claude Code when working in this repository.

## What this repo is

A course repository for "Master AI Agentic Engineering": a 6-week journey through building and deploying AI agents with the OpenAI Agents SDK, CrewAI, LangGraph, Google ADK, Pydantic AI, and MCP. It is mostly Jupyter notebooks, scripts, and guides, not a single application.

## Layout

- `1_foundations/` through `6_mcp/` - one folder per course week/module. Each holds lab notebooks and supporting code.
- `2_openai/`, `3_crewai/`, `4_langchain_langgraph/`, `5_agent_frameworks/`, `6_mcp/` - framework-specific modules.
- `guides/` - standalone guides (e.g. `09_ai_apis_and_ollama.ipynb`).
- `setup/` - platform setup instructions (`SETUP-PC.md`, `SETUP-mac.md`, `SETUP-linux.md`).
- `community_contributions/` - student-submitted work. Treat as independent; do not refactor it as part of unrelated changes.
- `assets/` - images used in the README and notebooks.

## Environment

- Python `>=3.12` (see `.python-version` and `pyproject.toml`).
- Dependencies are managed with `uv` and pinned in `uv.lock`. Add dependencies with `uv add <pkg>` so the lock file stays in sync; do not hand-edit `uv.lock`.
- API keys are read from a `.env` file (via `python-dotenv`). Never commit `.env` or hard-code keys in notebooks or scripts.

## Conventions

- Notebooks are the primary teaching medium. When editing a `.ipynb`, change only the cells you need and keep outputs out of diffs where possible (clear outputs before committing if the notebook was re-run).
- Match the style of the surrounding notebook or script: its comment density, naming, and markdown explanation style.
- Keep changes scoped to the module or lab being edited. Avoid cross-module refactors in a course repo, since students follow these exact files.

## Cost and safety

- Many labs call paid model APIs (OpenAI and others). Avoid running full notebooks end-to-end unless asked; prefer running a single cell or a small test.
- Do not add code that makes large numbers of API calls or runs long loops without an explicit limit.

## Git

- Main branch: `main`. Open PRs against `main`.
