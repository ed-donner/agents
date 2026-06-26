# Nicholas Dean - Week 2 (OpenAI Agents SDK)

A minimal deep-research agent: plan -> parallel search -> write.

- `deep_research.py` - a planner returns a structured `SearchPlan`, search agents run in
  parallel with `asyncio.gather`, a writer synthesizes one report, all inside a `trace()`.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python deep_research.py "your question"` (needs `OPENAI_API_KEY`; WebSearchTool bills per search).
