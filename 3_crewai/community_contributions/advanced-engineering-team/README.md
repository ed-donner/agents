# Advanced Engineering Team

A **multi-agent software engineering team** built with [CrewAI](https://www.crewai.com/). Each agent uses a different LLM with its own rate limit pool — no paid API keys required.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│ Engineering │ ──→ │   Backend    │ ──→ │   Frontend   │ ──→ │    QA      │
│    Lead     │     │   Engineer   │     │   Engineer   │     │  Engineer  │
│ (Design)    │     │  (accounts)  │     │   (Gradio)   │     │  (tests)   │
└─────────────┘     └──────────────┘     └──────────────┘     └────────────┘
     Groq                Groq                 Groq                Groq
  Llama 70B           Qwen 32B           Llama 4 Scout        Llama 70B
```

**Sequential process:** Design → Code → Frontend → Tests. Each task feeds into the next.

## Models (all free)

| Agent | Model | Provider |
|-------|-------|----------|
| Engineering Lead | `llama-3.3-70b-versatile` | Groq (12k TPM) |
| Backend Engineer | `qwen/qwen3-32b` | Groq |
| Frontend Engineer | `meta-llama/llama-4-scout-17b-16e-instruct` | Groq |
| QA Engineer | `llama-3.3-70b-versatile` | Groq (12k TPM) |

Each model sits in a separate rate limit pool — no shared token budgets.

## Features

- **Per-role LLM config** — `.env` driven, no hardcoded models
- **Docker code execution** — custom tool replaces CrewAI's buggy built-in Code Interpreter
- **Markdown-free output** — auto-strips thinking tags and markdown from generated files
- **CLI with stdin support** — pipe in custom requirements or use the built-in trading simulator spec
- **LangFuse observability** — every agent trace logged (configure via `.env`, free at cloud.langfuse.com)

## Quick Start

```bash
# 1. Clone & enter
cd community_contributions/advanced-engineering-team

# 2. Copy env template
cp .env.example .env
# Edit .env with your API keys (Groq required, OpenRouter optional)

# 3. Install
uv sync

# 4. Run
uv run advanced-engineering-team
```

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- **Groq API key** (free at console.groq.com)
- **Docker Desktop** (for backend & test code execution)
- **OpenRouter API key** (optional, for additional model providers)

## Generated Output

After running, `./output/` contains:

| File | Description |
|------|-------------|
| `accounts.py` | Trading account module with `Account` class |
| `accounts.py_design.md` | Design document from the Engineering Lead |
| `app.py` | Gradio UI for interacting with the account |
| `test_accounts.py` | 16 unittest tests (all pass) |

## Custom Requirements

```bash
# Pipe in custom requirements
echo "Build a todo list API with Flask" | uv run advanced-engineering-team

# Or use CLI args
uv run advanced-engineering-team \
  --module todo.py \
  --class-name TodoList
```

## Project Structure

```
advanced-engineering-team/
├── pyproject.toml
├── .env.example
├── src/
│   └── advanced_engineering_team/
│       ├── crew.py              # @CrewBase wiring
│       ├── main.py              # CLI entry point
│       ├── config/
│       │   ├── agents.yaml      # Role definitions
│       │   └── tasks.yaml       # Task chain
│       ├── llm/
│       │   ├── config.py        # Role→model env var mapping
│       │   └── factory.py       # LiteLLM object creation
│       └── tools/
│           └── docker_executor.py  # Docker code execution tool
└── output/                      # Generated files
```

## LangFuse

Set the `LANGFUSE_*` env vars in `.env` to trace every agent call. Free account at [cloud.langfuse.com](https://cloud.langfuse.com).

## Acknowledgements

Built as a community contribution for [Ed Donner's Master AI Agentic Engineering course](https://github.com/ed-donner/agents).
