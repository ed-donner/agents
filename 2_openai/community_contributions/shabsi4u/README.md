# Agentic Deep Research MVP

A local MVP of a deep research system built with the OpenAI Agents SDK.

`2_openai/deep_research` is reference-only. This folder contains an intentionally more agentic redesign with a dedicated orchestrator agent plus specialist worker agents.

## Layout

- `app.py`: CLI entrypoint
- `agents/`: orchestrator, clarifier, researcher, evaluator, writer
- `core/`: shared state and runtime guardrails
- `docs/implementation-plan.md`: local implementation plan

## Run

```bash
PYTHONPATH=2_openai/community_contributions/shabsi4u uv run python 2_openai/community_contributions/shabsi4u/app.py
```

## MVP Limitations

- The runtime shell still enforces guardrails such as max iterations and max searches.
- The app is CLI-first and asks for clarification answers interactively.
- The implementation is intentionally small and favors clarity over feature breadth.
