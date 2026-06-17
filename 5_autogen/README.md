# Week 5 — AutoGen

**Goal:** Explore Microsoft AutoGen's two layers — the high-level **AgentChat** API for rapid development, and the low-level **Core** runtime for distributed, message-driven architectures.

---

## Labs

### Lab 1 — AgentChat Basics (`1_lab1.ipynb`)
- AutoGen's three-step pattern: **Model → Message → Agent**
- Creating a `ModelClient` and sending `TextMessage` objects
- Defining an `AssistantAgent` with function-based tools
- Building an airline booking agent that queries a **SQLite database** of ticket prices
- Understanding the AgentChat API as the fastest way to get an agent running

### Lab 2 — Multimodal, Teams & MCP Integration (`2_lab2.ipynb`)
- Sending `MultiModalMessage` objects containing images for visual analysis
- Using `output_content_type` parameter for **structured Pydantic outputs**
- Adapting LangChain tools for AutoGen via `LangChainToolAdapter` — cross-framework tool reuse
- Grouping agents into a `RoundRobinGroupChat` **team** with termination conditions
- Integrating **MCP (Model Context Protocol)** tools directly into AutoGen agents

### Lab 3 — AutoGen Core: Message-Driven Architecture (`3_lab3.ipynb`)
- Shifting to the lower-level **AutoGen Core** API
- Creating a `SingleThreadedAgentRuntime` as the agent execution environment
- Subclassing `RoutedAgent` and using `@message_handler` decorators to respond to specific message types
- Agents register with the runtime and communicate **asynchronously** via message passing
- Rock-paper-scissors demo: two agents interacting purely through the message bus

### Lab 4 — Distributed Runtime with gRPC (`4_lab4.ipynb`)
- Scaling beyond a single process with `GrpcWorkerAgentRuntimeHost`
- Agents deployed across **multiple processes or machines**, communicating over **gRPC**
- One agent delegating subtasks to agents in separate worker processes
- Parallel pros/cons analysis: two remote agents working simultaneously, results collected by the host
- Understanding when and why to use distributed vs. single-threaded runtime

---

## Supporting Modules

| File | Purpose |
|------|---------|
| `agent.py` | Reusable agent definitions used across labs |
| `creator.py` | Factory / builder patterns for agent construction |
| `world.py` | Simulated environment for multi-agent interaction |
| `messages.py` | Custom message type definitions |
| `database.py` | SQLite database setup and queries (airline tickets) |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| AgentChat API | High-level API: `AssistantAgent`, `TextMessage`, `ModelClient` |
| Core API | Low-level: `RoutedAgent`, `@message_handler`, runtime registration |
| `SingleThreadedAgentRuntime` | In-process runtime for local multi-agent systems |
| `GrpcWorkerAgentRuntimeHost` | Distributed runtime for cross-process/machine agents |
| `MultiModalMessage` | Message type supporting text + images |
| `output_content_type` | Enforces Pydantic structured output from an agent |
| `LangChainToolAdapter` | Wraps LangChain tools for use in AutoGen agents |
| `RoundRobinGroupChat` | Team pattern where agents take turns responding |
| `@message_handler` | Decorator binding a method to a specific incoming message type |
| MCP integration | Using Model Context Protocol tools natively within AutoGen |

---

## Files

```
5_autogen/
├── 1_lab1.ipynb     # AgentChat basics + SQLite airline booking
├── 2_lab2.ipynb     # Multimodal + teams + MCP integration
├── 3_lab3.ipynb     # AutoGen Core runtime + message-driven architecture
├── 4_lab4.ipynb     # Distributed gRPC runtime
├── agent.py         # Shared agent definitions
├── creator.py       # Agent factory helpers
├── world.py         # Multi-agent simulation environment
├── messages.py      # Custom message types
└── database.py      # SQLite setup for airline booking demo
```

---

## Setup

```bash
pip install -r requirements.txt
```

Pinned versions (tested May 2026):

```
autogen-agentchat>=0.4.9
autogen-ext[openai]>=0.4.9
openai>=1.78.0
python-dotenv>=1.1.0
gradio>=5.29.1
# For Lab 4 distributed runtime:
# autogen-ext[grpc]>=0.4.9
```

Requires `OPENAI_API_KEY` in `.env`. Lab 2 optionally uses `SERPER_API_KEY` for web search tools.  
Lab 1 and 3 optionally use Ollama (free, local) — install from [ollama.com](https://ollama.com).

> **Cost guide:** All labs use `gpt-4o-mini` (~$0.002–0.10/run). The Ollama option (llama3.2) is free. Cost banners are at the top of each notebook.
