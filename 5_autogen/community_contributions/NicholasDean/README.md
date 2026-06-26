# Nicholas Dean - Week 5 (AutoGen)

A minimal two-agent reflection team.

- `reflection_team.py` - a Writer drafts, a Critic gives feedback, a `RoundRobinGroupChat`
  alternates them, and `TextMentionTermination("APPROVE")` ends the loop once the Critic is
  satisfied. The conversation streams to the terminal.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python reflection_team.py "your task"` (needs `OPENAI_API_KEY`).
