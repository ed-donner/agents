# Week 5 — AutoGen

Microsoft's framework, in two layers. **AgentChat** = conversational agents that take turns in a
team; **Core** = a lower-level async message-passing runtime for decoupled (even distributed) agents.

- **AgentChat primitives:**
  - **`AssistantAgent(name, model_client, system_message, tools=)`** — an agent; tools are plain
    Python callables. `output_content_type=` for structured (Pydantic) output.
  - **`OpenAIChatCompletionClient(model=...)`** (from `autogen_ext.models.openai`) is the model
    client; there's `OllamaChatCompletionClient` too.
  - Run one agent with **`await agent.on_messages([TextMessage(...)], CancellationToken())`**; run a
    team with **`await team.run(task=...)`** / `team.run_stream(...)`. Everything is **async**.
- **Teams:** **`RoundRobinGroupChat([a, b], termination_condition=...)`** alternates agents;
  **`SelectorGroupChat`** picks the best next speaker.
- **Termination is first-class:** `TextMentionTermination("APPROVE")`, `MaxMessageTermination(n)` —
  end logic lives outside the agents, so teams are reusable.
- **AutoGen Core (lower level):** a **`SingleThreadedAgentRuntime`** (or gRPC distributed runtime)
  delivers messages; agents subclass **`RoutedAgent`** and handle typed messages with
  **`@message_handler`**; register types with `Agent.register(runtime, "type", factory)` and address
  them by `AgentId(type, key)`. This is peer-to-peer messaging, not a fixed DAG.
- The course capstone is an **"agent world"**: a Creator agent uses an LLM to *generate new agent
  files at runtime*, registers them on a distributed runtime, and they bounce business ideas off each
  other — a self-growing mesh of agents.

**Built:** `reflection_team.py` — a minimal **reflection** team: a Writer drafts, a Critic gives
feedback, `RoundRobinGroupChat` alternates them, and `TextMentionTermination("APPROVE")` ends the
loop once the Critic is satisfied. The whole back-and-forth streams to the terminal via `Console`.

## Distilled learning

**ELI5:** Where CrewAI gives each agent a job description and LangGraph draws a flowchart, AutoGen
just sits agents around a table and lets them *talk*. You decide the turn order (round-robin) and a
stop signal (a magic word like "APPROVE"), and they converse until done. Underneath, AutoGen Core is
a postal service: agents send typed messages to each other's address — no central script.

```python
writer = AssistantAgent("writer", model_client=client, system_message="Write and revise...")
critic = AssistantAgent("critic", model_client=client, system_message="Critique; say APPROVE when good.")
team = RoundRobinGroupChat([writer, critic], termination_condition=TextMentionTermination("APPROVE"))
await team.run(task="Write a tagline.")     # they alternate until the critic approves
```
