# DevSwarm (Week 3)

CrewAI "self-evolving" software agency: researches requirements, dynamically hires specialist agents/tasks at runtime, writes code, and QA-verifies in a sandbox.

Week 3 patterns: hierarchical crews, dynamic agent injection, Serper research, code execution tools, cost guardrails.

## Loop

1. Reconnaissance (Architect + Serper)
2. Self-assembly (hire specialist agents/tasks)
3. Sandboxed execution
4. Self-healing QA / refactor

## Setup

```bash
cd 3_crewai/community_contributions/Sama-ndari_dev_swarm
uv sync
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
SERPER_API_KEY=...
```

## Run

```bash
uv run run_crew
```

Full project (optional): https://github.com/Sama-ndari/dev-swarm-autonomous-agency

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
