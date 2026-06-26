# Nicholas Dean - Week 4 (LangGraph)

A minimal tool-using agent drawn as an explicit graph.

- `graph_agent.py` - a State with the `add_messages` reducer, a worker LLM + `ToolNode`, a
  conditional edge that loops until the model stops calling tools, and a `MemorySaver`
  checkpointer so a `thread_id` remembers the conversation.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python graph_agent.py` (needs `OPENAI_API_KEY`).
