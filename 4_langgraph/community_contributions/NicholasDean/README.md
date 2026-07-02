# Nicholas Dean - Week 4 (LangGraph)

Sidekick - a worker that is checked by an evaluator until the work passes.

- `sidekick.py` - a worker LLM (with `calculator` and `save_note` tools) does the task against a
  `success_criteria`; an **evaluator** node then grades the result with structured output
  (`EvaluatorOutput`) and either ends (criteria met, or it needs the user) or routes back to the
  worker with feedback to try again. Built on `add_messages` state, a `ToolNode`, two conditional
  edges, and a `MemorySaver` checkpointer.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python sidekick.py` (needs `OPENAI_API_KEY`). Writes to a local `sandbox/` folder.
