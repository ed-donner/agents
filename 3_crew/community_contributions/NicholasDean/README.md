# Nicholas Dean - Week 3 (CrewAI)

A minimal sequential crew in one file: Researcher -> Writer, with context passing.

- `research_crew.py` - the Researcher finds 5 key points on a topic; the Writer turns them
  into a one-page briefing (its task lists the research task as `context`). Writes `briefing.md`.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python research_crew.py "your topic"` (needs `OPENAI_API_KEY` and `crewai` installed).
