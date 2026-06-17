# Week 4 — LangGraph

**Goal:** Model agents as explicit **state machines** — nodes, edges, and typed state — giving full, transparent control over every step of agent execution.

---

## Labs

### Lab 1 — StateGraph Basics (`1_lab1.ipynb`)
- Creating a `StateGraph` with a `TypedDict` or Pydantic state object
- Writing nodes as plain Python functions that receive and return state
- Connecting nodes with `START` / `END` edges
- Key insight: LangGraph works with *any* Python code — not just LLMs — making it a general-purpose workflow engine

### Lab 2 — Tool Integration & Persistent Memory (`2_lab2.ipynb`)
- Binding tools to LLMs with `.bind_tools()`
- Routing with **conditional edges** — branching on whether `tool_calls` are present in the LLM response
- Using `ToolNode` to automatically execute tool calls and return results to state
- Adding **persistent memory via checkpointing**:
  - `MemorySaver` — in-memory checkpoints for development
  - `SqliteSaver` — SQLite-backed persistence across sessions
- Using `thread_id` to maintain separate conversation histories per user

### Lab 3 — Async Execution & Browser Automation (`3_lab3.ipynb`)
- Running graphs asynchronously with `graph.ainvoke()`
- Integrating LangChain's `PlayWrightBrowserToolkit` for real browser automation (clicking, scraping)
- Using `nest_asyncio` to run async code inside Jupyter notebooks
- How LangGraph manages long tool sequences without explicit loop management

### Lab 4 — Multi-Node Sidekick with Evaluator Pattern (`4_lab4.ipynb`)
- Building a three-node "Sidekick" agent system:
  - **Worker node** — uses tools to attempt the task
  - **Evaluator node** — LLM assesses success with a structured `EvaluatorOutput` (Pydantic)
  - **Conditional routing** — retry the worker or terminate based on evaluator verdict
- Complex state management across multiple nodes
- Integrating a **Gradio UI** with `asyncio` for a live chat interface
- The evaluator pattern — using a separate LLM node to judge quality and drive retries

---

## App — Sidekick (`sidekick.py` + `sidekick_tools.py`)

A production-style assistant that brings the multi-node evaluator graph into a deployable Gradio application:
- Worker executes tool calls; evaluator decides if the result is satisfactory
- If not, the graph loops back for another attempt — automatically retrying up to a limit
- All tools are defined in `sidekick_tools.py` and registered with the worker node

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| `StateGraph` | Directed graph where each node reads/writes a shared typed state |
| `TypedDict` / Pydantic state | Strongly typed state object passed between nodes |
| Nodes | Plain Python functions — can be LLM calls, tools, or any logic |
| Edges | Connections between nodes; `START` and `END` are special built-ins |
| Conditional edges | Branch to different nodes based on state content |
| `ToolNode` | Built-in node that executes tool calls found in LLM output |
| `MemorySaver` | In-memory checkpointing for development/testing |
| `SqliteSaver` | Persistent SQLite checkpointing across process restarts |
| `thread_id` | Key for isolating separate conversation sessions in memory |
| `graph.ainvoke()` | Async graph execution |
| Evaluator pattern | Separate node judges output quality and routes to retry or finish |

---

## Files

```
4_langgraph/
├── 1_lab1.ipynb          # StateGraph basics
├── 2_lab2.ipynb          # Tools + conditional edges + checkpointing
├── 3_lab3.ipynb          # Async + browser automation
├── 4_lab4.ipynb          # Multi-node Sidekick + evaluator pattern
├── sidekick.py           # Gradio app using the Sidekick graph
└── sidekick_tools.py     # Tool definitions for the Sidekick agent
```

---

## Setup

```bash
pip install -r requirements.txt
```

Pinned versions (tested May 2026):

```
openai>=1.78.0
langchain>=0.3.23
langchain-openai>=0.3.14
langgraph>=0.3.34
langchain-community>=0.3.21
python-dotenv>=1.1.0
gradio>=5.29.1
playwright>=1.52.0
```

After installing, run `playwright install chromium` once for browser automation (Lab 3 and 4).

Requires `OPENAI_API_KEY` in `.env`. Lab 2 optionally uses `SERPER_API_KEY` for web search and `PUSHOVER_TOKEN`/`PUSHOVER_USER` for push notifications.

> **Cost guide:** All labs use `gpt-4o-mini` (~$0.01–0.20/run depending on how many tool calls the agent makes). Cost banners are at the top of each notebook.
