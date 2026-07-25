# Microsoft Agent Framework

**Author:** Niket Sharma — sharma.niket@gmail.com

Microsoft Agent Framework is the direct successor to both **AutoGen** and **Semantic Kernel**, combining AutoGen's simple agent abstractions with Semantic Kernel's enterprise features (type safety, middleware, telemetry, session management).

## Setup

```bash
pip install agent-framework agent-framework-openai
```

Requires `OPENAI_API_KEY` in your environment (`.env` file supported via `python-dotenv`).

## Labs

### [Lab 1 — Basics](1_lab1_ms_agent_basics.ipynb)
Core building blocks of the framework.
- `OpenAIChatCompletionClient` and `client.as_agent()`
- Running agents with `await agent.run()`
- Token-by-token streaming with `stream=True`
- Attaching Python functions as tools (auto JSON schema from type hints + docstrings)
- Multiple tools and the `@tool` decorator
- SQLite-backed ticket price database used throughout the labs

### [Lab 2 — Advanced Features](2_lab2_ms_agent_advanced.ipynb)
- **Structured outputs** — constrain responses to a Pydantic model via `output_type=`
- **Multi-turn sessions** — `agent.create_session()` preserves conversation history
- **Image inputs** — multi-modal messages with `Content.from_data()`
- **Multi-agent hand-off** — sequential orchestration between agents in plain Python
- **Agent as Tool** — `agent.as_tool()` lets an orchestrator call another agent like a function
- **MCP tools** — `MCPStdioTool` integrates any Model Context Protocol server

### [Lab 3 — Workflows](3_lab3_ms_agent_workflows.ipynb)
Graph-based orchestration for deterministic, multi-step pipelines.
- `Executor` class with the `@handler` decorator for typed message routing
- `@executor` decorator for function-based executors (no class needed)
- `WorkflowBuilder` to assemble executors and edges into a directed graph
- AI agents wrapped inside executors (summarise → translate pipeline)
- Streaming workflow events (`executor_started`, `executor_completed`, `output`)
- Rock, Paper, Scissors demo: Judge coordinates two Player executors

### [Lab 4 — Advanced Multi-Agent Workflows](4_lab4_ms_agent_multiagent.ipynb)
Complex orchestration patterns using the Workflow engine.
- **Fan-out / fan-in** — Splitter sends one input to Pros + Cons agents in parallel; Merger collects results
- **Debate + Judge** — extends fan-out with a JudgeExecutor for final verdict
- **Dynamic fan-out** — TopicExpander breaks a topic into sub-questions, Researcher answers each, Synthesizer produces a report
- Comparison table: AutoGen Distributed (gRPC) vs Microsoft Agent Framework (zero infrastructure)

### [Lab 5 — Agent Skills](5_lab5_ms_agent_skills.ipynb)
Portable domain-knowledge packages that use progressive disclosure to avoid token waste.
- **File-based skills** — `SKILL.md` directories with `references/` and `scripts/` subdirectories
- **Code-defined skills** — `Skill` objects in Python with `@skill.resource` and `@skill.script`
- **Dynamic resources** — decorated functions called fresh each time the agent reads them
- **Combining** file-based and code-defined skills in one `SkillsProvider`
- **Script approval** — `require_script_approval=True` gates script execution behind human confirmation
- **Runtime injection** — `function_invocation_kwargs` forwards per-request context (e.g. currency) to skill functions via `**kwargs`

### [Lab 6 — Memory & A2A Hosting](6_lab6_ms_agent_memory_a2a.ipynb)
Production-ready memory and inter-agent communication.
- **Custom `ContextProvider`** — `before_run` / `after_run` hooks with a per-session `state` dict
- **`InMemoryHistoryProvider`** — configurable history buffering (`load_messages`, `store_inputs`, `store_outputs`, `store_context_messages`)
- **`FileHistoryProvider`** — JSONL persistence across process restarts; session ID links runs
- **A2A server** — `A2AExecutor` + `A2AStarletteApplication` exposes any agent over HTTP (see [`sandbox/travel_a2a_server.py`](sandbox/travel_a2a_server.py))
- **A2A client** — `A2AAgent(url=...)` connects to any A2A-compliant service with the same `.run()` API
- **Streaming from remote** — `await remote_agent.run(..., stream=True)`
- **Remote agent as tool** — `remote_agent.as_tool()` lets a local orchestrator delegate to a remote agent transparently

## Folder Structure

```
7_ms_agent_framework/
├── 1_lab1_ms_agent_basics.ipynb
├── 2_lab2_ms_agent_advanced.ipynb
├── 3_lab3_ms_agent_workflows.ipynb
├── 4_lab4_ms_agent_multiagent.ipynb
├── 5_lab5_ms_agent_skills.ipynb
├── 6_lab6_ms_agent_memory_a2a.ipynb
├── tickets.db                          # SQLite DB with city round-trip prices
├── sandbox/
│   └── travel_a2a_server.py            # Standalone A2A server (uvicorn/Starlette)
├── skills/
│   └── travel-policy/
│       ├── SKILL.md                    # Skill instructions + frontmatter
│       ├── references/
│       │   └── refund-policy.md        # Full refund rules (read via read_skill_resource)
│       └── scripts/
│           └── estimate_refund.py      # Refund calculator (run via run_skill_script)
└── chat_history/
    └── demo-session-001.jsonl          # Persisted session from FileHistoryProvider demo
```

## Key Concepts at a Glance

| Concept | API |
|---|---|
| Create agent | `client.as_agent(name=..., instructions=..., tools=...)` |
| Run agent | `await agent.run("...")` |
| Stream | `async for chunk in agent.run("...", stream=True)` |
| Session | `session = agent.create_session(); agent.run(..., session=session)` |
| Workflow | `WorkflowBuilder(start_executor=...).add_edge(...).build()` |
| Agent as Tool | `agent.as_tool(name=..., arg_name=...)` |
| Skills | `SkillsProvider(skill_paths=..., skills=[...])` |
| Memory | `ContextProvider` subclass with `before_run` / `after_run` |
| A2A server | `A2AExecutor(agent)` + `A2AStarletteApplication` |
| A2A client | `A2AAgent(name=..., url=...)` |
