# Nicholas Dean - Week 5 (AutoGen)

Both AutoGen layers - the high-level AgentChat team and the lower-level autogen-core runtime.

- `reflection_team.py` (**AgentChat**) - a Writer drafts, a Critic gives feedback, a
  `RoundRobinGroupChat` alternates them, and `TextMentionTermination("APPROVE")` ends the loop once
  the Critic is satisfied. Streams to the terminal.
- `agent_world.py` (**autogen-core**) - a `SingleThreadedAgentRuntime` delivers typed messages
  between `RoutedAgent`s (`@message_handler`). A coordinator `send_message`s an `Ask` to several
  LLM-backed domain agents and collects their `Idea` replies - the message-passing backbone the
  distributed agent-world capstone is built on.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python reflection_team.py "your task"` or `uv run python agent_world.py`
(needs `OPENAI_API_KEY`).
