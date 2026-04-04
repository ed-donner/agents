# Week 4: LangGraph — Learning Summary

## Key Concepts Defined

| Term | Definition |
|---|---|
| **StateGraph** | LangGraph's core class for defining a graph of nodes (functions) connected by edges. Compiled before use. |
| **State** | A typed schema (Pydantic `BaseModel` or `TypedDict`) that flows through the graph, shared across all nodes. |
| **Reducer** | A function that controls how a state field is updated. `add_messages` merges incoming messages instead of overwriting. |
| **Node** | A Python function (sync or async) that receives the current state and returns an updated partial state. |
| **Edge** | A directed connection between nodes. Can be static (`add_edge`) or conditional (`add_conditional_edges`). |
| **`START` / `END`** | Special LangGraph constants marking the graph's entry and exit points. |
| **`compile()`** | Finalizes the graph and returns a runnable. Accepts an optional `checkpointer` for memory. |
| **`invoke` / `ainvoke`** | Synchronous / asynchronous methods to run the graph with an initial state. |
| **`bind_tools()`** | Attaches tool schemas to an LLM so it can propose tool calls in its output. |
| **`ToolNode`** | A prebuilt LangGraph node that executes any tool calls present in the last message. |
| **`tools_condition`** | A prebuilt router: sends flow to `tools` if tool calls exist, otherwise to `END`. |
| **Tool loop** | The `chatbot → tools → chatbot` cycle that lets the LLM iteratively use tools. |
| **Checkpointer** | Persists graph state between invocations. `MemorySaver` stores in RAM; `SqliteSaver` stores to disk. |
| **`thread_id`** | A key in `config["configurable"]` that scopes persisted state to a specific conversation thread. |
| **`get_state` / `get_state_history`** | Methods to inspect or replay a graph's past states from a checkpointer. |
| **`nest_asyncio`** | Patches Python's event loop to allow nested `await` calls — necessary for async LangGraph in Jupyter. |
| **`PlayWrightBrowserToolkit`** | LangChain wrapper around async Playwright that exposes browser navigation/extraction as LLM tools. |
| **Structured output** | `llm.with_structured_output(Schema)` forces the LLM to return a validated Pydantic object instead of free text. |
| **Worker LLM** | An agent node responsible for doing the actual task (browsing, coding, writing). |
| **Evaluator LLM** | A second LLM node that assesses the worker's output and decides: retry, stop, or ask the user. |
| **Self-critique / quality loop** | A graph topology where an evaluator can loop the worker back to retry until success criteria are met. |
| **`FileManagementToolkit`** | LangChain toolkit giving the agent scoped read/write access to a local directory (sandbox). |
| **`PythonREPLTool`** | Tool that executes Python code in-process and returns stdout — enables code-executing agents. |
| **`sidekick_id`** | A UUID used as `thread_id` to uniquely identify and persist one Sidekick agent's conversation. |
| **`gr.State`** | Gradio session-scoped state — used here to hold the live `Sidekick` instance per browser session. |
| **`delete_callback`** | Gradio hook called when a `gr.State` is garbage-collected, used to clean up browser/Playwright resources. |

---

## What Each File Teaches

### `1_lab1.ipynb` — LangGraph Fundamentals
- How to define a `StateGraph` from scratch with typed state, nodes, and edges.
- The role of **reducers** (`add_messages`) in managing list-based state fields.
- Difference between LLM-driven and plain Python nodes — LangGraph is not always AI.
- How to visualize a compiled graph as a Mermaid diagram.
- How to wire a graph into a **Gradio `ChatInterface`** for interactive testing.

### `2_lab2.ipynb` — Tools + Persistent Memory
- How to wrap capabilities as `Tool` objects and bind them to an LLM with `bind_tools`.
- How to build the standard **tool loop** using `ToolNode` and `tools_condition`.
- The difference between **super-step state merging** (within one invoke) and **cross-invoke memory** (checkpointing).
- How to use `MemorySaver` and `SqliteSaver` as checkpointers for in-memory vs persistent threads.
- How `thread_id` in `configurable` isolates separate conversation sessions.
- How to inspect and branch state history with `get_state` / `get_state_history`.

### `3_lab3.ipynb` — Async Execution + Browser Automation
- How to convert a synchronous LangGraph to fully **async** using `ainvoke` and `arun`.
- How `nest_asyncio` resolves event loop conflicts in Jupyter notebooks.
- How to set up `PlayWrightBrowserToolkit` with an async Playwright browser for live web interaction.
- How to combine browser tools with other tools in the same tool loop.
- That the core graph pattern (tool loop + checkpointing) scales to async browser agents with minimal changes.

### `4_lab4.ipynb` — Evaluator Loop + Structured Output
- How to use `with_structured_output(Pydantic Schema)` to get typed, validated decisions from an LLM.
- How to design a **two-LLM architecture**: a worker that acts and an evaluator that judges.
- How to build **custom conditional routers** (`worker_router`, `route_based_on_evaluation`) beyond the prebuilt `tools_condition`.
- How to store evaluator metadata (feedback, flags) as separate scalar fields in `State`.
- How a **self-critique loop** can automate quality control without human-in-the-loop approval gates.
- How to surface worker replies and evaluator reasoning in a **Gradio Blocks** UI.

### `sidekick.py` — Reusable Agent Class
- How to encapsulate a LangGraph agent as a Python class with a clean async lifecycle (`setup`, `run_superstep`, `cleanup`).
- How to enrich system prompts with runtime context (current datetime, tool-specific instructions).
- How to handle **Playwright resource cleanup** gracefully in both running-loop and non-running-loop scenarios.
- How to use `sidekick_id` as a stable `thread_id` across multiple `run_superstep` calls.

### `sidekick_tools.py` — Tool Registry
- How to build and return Playwright browser tools with explicit lifecycle handles (`browser`, `playwright`).
- How to assemble a diverse, production-grade **toolbelt**:
  - Sandboxed filesystem access (`FileManagementToolkit`)
  - In-process code execution (`PythonREPLTool`)
  - Web search (Google Serper)
  - Encyclopedia lookup (`WikipediaQueryRun`)
  - Push notifications (Pushover via `requests`)
- How to separate tool construction from graph logic for modularity and testability.

### `app.py` — Gradio Application Entry Point
- How to structure a **Gradio Blocks** app that manages a stateful async agent.
- How `ui.load` triggers one-time async setup (Playwright + graph) before the user interacts.
- How `gr.State` holds a live agent instance scoped to the browser session.
- How `delete_callback` enables proper **resource cleanup** when a session ends.
- How to implement a reset flow that tears down and reinitialises the agent cleanly.

---

## Progression Arc

```
Lab 1               Lab 2                  Lab 3                   Lab 4
Minimal graph  →  Tools + Memory  →  Async + Browser  →  Evaluator loop
(StateGraph,       (bind_tools,         (ainvoke,             (structured output,
 nodes, edges,      ToolNode,            Playwright,           worker/evaluator,
 add_messages)      checkpointing)       nest_asyncio)         quality loop)
                                                                      ↓
                                              sidekick.py + sidekick_tools.py + app.py
                                              (production class, rich toolbelt, Gradio app)
```

---

## Deep Dive: Understanding `State` — The Heart of LangGraph

### ELI5 (Explain Like I'm 5)

Imagine you and your friends are playing a game of telephone where you pass a **notebook** around a circle.
Every person (node) reads the notebook, adds or changes something on it, and passes it to the next person.
The notebook is the **State** — it's the single shared object everyone reads from and writes to.
Nobody works in isolation; they all depend on what's already written in the notebook.

That's exactly what LangGraph State is: a **shared notebook** that flows through every node in the graph.

---

### What Is State, Formally?

**State** is the typed data structure that:
1. Is defined **before** the graph is built (it's the schema).
2. Is passed **into** every node as input.
3. Is partially **returned** by every node as output (nodes return only what changed).
4. Is **merged** back into the full state by LangGraph automatically using reducer functions.

State is not a copy — it is **the single source of truth** for the entire graph execution.
Every node sees the same state, and every node's output is applied back to that same state.

---

### How to Define State

LangGraph supports three schema formats, in order of recommendation:

**1. `TypedDict` (most common — fastest, IDE-friendly)**
```python
from typing import TypedDict

class State(TypedDict):
    messages: list
    current_step: str
```

**2. `dataclass` (adds default values)**
```python
from dataclasses import dataclass, field

@dataclass
class State:
    messages: list = field(default_factory=list)
    current_step: str = "start"
```

**3. Pydantic `BaseModel` (adds runtime validation, but slower)**
```python
from pydantic import BaseModel

class State(BaseModel):
    messages: list = []
    current_step: str = "start"
```

---

### The Critical Rule: Nodes Return Partial Updates, Not Full State

This is one of the most important things to understand.
When a node finishes, it does **not** return the entire State object.
It returns **only the fields it changed** as a plain dict.

```python
# Node receives the full state
def my_node(state: State) -> dict:
    # Only returns the field that changed
    return {"current_step": "done"}
    # LangGraph applies this partial update to the full state
```

LangGraph takes that partial dict and **merges** it into the existing state.
Fields not mentioned in the return value are left completely untouched.

---

### State Channels and Reducers

Every field in the State schema is called a **channel**.
Each channel has a **reducer** — a rule that defines *how* an incoming update is applied to the existing value.

#### Default Reducer: Overwrite (Last Write Wins)
If you declare a field with no special annotation, any new value simply **replaces** the old one:

```python
class State(TypedDict):
    foo: int   # new value always overwrites old value
```

If `foo` is `1` and a node returns `{"foo": 2}`, it becomes `2`. Simple.

#### Custom Reducer: `add_messages` (Append + Deduplicate)
For a list of messages, overwriting is disastrous — you'd lose conversation history.
Instead, annotate the field with a reducer using `Annotated`:

```python
from typing import Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
```

Now when a node returns `{"messages": [new_message]}`, LangGraph **appends** the new message
to the existing list instead of replacing it. `add_messages` also handles deduplication by
message ID, so replaying or editing messages works correctly.

You can use any function as a reducer:

```python
from operator import add

class State(TypedDict):
    scores: Annotated[list[int], add]   # always concatenates
```

#### The `MessagesState` Shortcut
Because message lists are so common, LangGraph ships a prebuilt State:

```python
from langgraph.graph import MessagesState

# Equivalent to: messages: Annotated[list[AnyMessage], add_messages]
# Subclass to add more fields:
class MyState(MessagesState):
    documents: list[str]
    success: bool
```

---

### Advanced: Multiple State Schemas

For complex graphs, you can split State into roles:

| Schema | Purpose |
|---|---|
| `InputState` | Constrains what the *caller* provides — external-facing |
| `OutputState` | Constrains what the *graph returns* — external-facing |
| `OverallState` | Full internal schema — all nodes share this |
| `PrivateState` | Internal-only fields for node-to-node comms, hidden externally |

```python
builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
```

Nodes can read from their declared input type and write to any channel in `OverallState`.

---

### How State Relates to Every Other Key Term in This Summary

State is the **connective tissue** of everything else in LangGraph:

| Term (from Summary) | How State Is Involved |
|---|---|
| **StateGraph** | Parameterized *by* your State class: `StateGraph(MyState)`. The graph and State are inseparable. |
| **Reducer** | Attached *to* State fields via `Annotated`. Defines how node outputs are merged into State. |
| **Node** | Receives State as input, returns partial State as output. Nodes exist *to transform* State. |
| **Edge / Conditional Edge** | Routing functions receive the *current State* and decide the next node based on it. State drives control flow. |
| **`START` / `END`** | `START` triggers the initial State injection; `END` marks where the final State snapshot is captured. |
| **`compile()`** | Locks in the State schema and validates the graph. The `checkpointer` is attached here to *persist* State. |
| **`invoke` / `ainvoke`** | You pass the *initial State* dict here. The graph runs and returns the *final State* dict. |
| **`bind_tools()`** | Tool call results are injected back into State's `messages` channel via `add_messages`. |
| **`ToolNode`** | Reads tool call requests from `state["messages"][-1]`, executes them, and writes results back to `messages`. |
| **`tools_condition`** | Inspects `state["messages"][-1]` to check if tool calls are present — pure State inspection. |
| **Tool loop** | Each loop iteration is a State mutation: user message → AI message (with tool call) → tool result message. |
| **Checkpointer** | Saves a **snapshot of State** after every super-step. Memory *is* persisted State. |
| **`thread_id`** | The key used to look up the right State snapshot from the checkpointer's storage. |
| **`get_state` / `get_state_history`** | Returns `StateSnapshot` objects — frozen copies of State at past super-step boundaries. |
| **Structured output** | The Pydantic schema used in `with_structured_output(...)` mirrors how State schemas work — typed, validated output written into State fields. |
| **Worker LLM** | Reads task context from State and writes AI messages back to State's `messages` channel. |
| **Evaluator LLM** | Reads the full conversation from State, writes back `feedback_on_work`, `success`, `user_input_needed` — all scalar State channels. |
| **Self-critique loop** | Only possible because the evaluator's decisions (success flags) *live in State*, and conditional edges can read them to route. |
| **`sidekick_id`** | Used as `thread_id` to scope a persistent State snapshot to one Sidekick instance across calls. |
| **`gr.State`** | *Not* the same concept — Gradio's session storage. Holds the live `Sidekick` Python object, not the LangGraph State. |

---

### The State Lifecycle in One Graph Run

```
graph.invoke({"messages": [HumanMessage("hello")]}, config)
        │
        ▼
┌──────────────────────────────────────┐
│  Initial State injected at START     │
│  { messages: [HumanMessage("hello")] }│
└────────────────┬─────────────────────┘
                 │  (checkpointer saves snapshot #0)
                 ▼
          ┌─────────────┐
          │  chatbot    │  ← reads full State
          │    node     │  → returns {"messages": [AIMessage(...)]}
          └──────┬──────┘
                 │  LangGraph applies reducer: add_messages
                 │  (checkpointer saves snapshot #1)
                 ▼
          State is now:
          { messages: [HumanMessage("hello"), AIMessage("hi!")] }
                 │
        [tools_condition reads State]
                 │  No tool calls → route to END
                 ▼
          Final State returned to caller
```

Every arrow in this diagram is a State transition.
The graph *is* a machine that transforms State, step by step.

---

### Common Pitfalls

| Mistake | Why It Breaks | Fix |
|---|---|---|
| Returning full State from a node | Not an error, but redundant and fragile | Return only changed fields as a plain dict |
| Using plain `list` for messages without `add_messages` | Each node invocation **overwrites** message history | Use `Annotated[list, add_messages]` |
| Forgetting `thread_id` when using a checkpointer | Checkpointer cannot save or load State without it | Always pass `config={"configurable": {"thread_id": "..."}}` |
| Using `Command(update=...)` as `invoke()` input to continue a conversation | Resumes from last checkpoint, graph appears stuck | Pass a plain dict input for new turns |
| Storing a live object (e.g. LLM instance) in State | State must be serializable for checkpointing | Keep non-serializable objects outside State (e.g. in the node's closure) |

---

## Deep Dive: Super-Steps, State Merging, and Cross-Invoke Memory

These three concepts are closely related and build on each other. They explain *how* LangGraph actually executes a graph and *how* it remembers things.

---

### 1. What Is a Super-Step?

A **super-step** is one single "tick" or "heartbeat" of the graph engine — a discrete unit of execution where all currently scheduled nodes run (potentially in parallel), and their outputs are collected.

Think of it like a **round in a board game**: everyone takes their turn simultaneously in one round, then the board is updated, then the next round begins.

LangGraph's execution engine is inspired by Google's **Pregel** system. The rules are:

- At the start of a graph run, all nodes are **inactive**.
- A node becomes **active** when it receives a message/state on its incoming edge.
- All active nodes in the same round execute as one **super-step**.
- After they all finish, their outputs are merged into the State.
- That updated State triggers the next round of nodes → next super-step.
- The graph halts when all nodes are inactive and no messages are in transit.

#### Example: Simple Sequential Graph

```
START → node_a → node_b → END
```

This produces **4 super-steps** (4 checkpoints saved):

| Super-step | What happens |
|---|---|
| -1 | Input is injected at `__start__` |
| 0 | `node_a` runs |
| 1 | `node_b` runs |
| 2 | Graph reaches `END`, execution halts |

#### Example: Parallel Graph

```
START → node_a → node_b  ← both in same super-step
              → node_c  ←
```

`node_b` and `node_c` run **in parallel within the same super-step** because they're both triggered by `node_a` simultaneously.

#### Why It Matters

- A **checkpoint** is saved at each super-step boundary — this is the unit of persistence.
- You can only **replay or resume** from a super-step boundary, not from mid-node.
- The **recursion limit** counts super-steps, not individual node calls.

---

### 2. What Is Super-Step State Merging?

**Super-step state merging** is what happens *within a single `invoke()` call* — specifically, how the outputs from all nodes in a super-step are combined back into the shared State.

#### The Rule

When a super-step ends, LangGraph collects all partial dicts returned by the nodes that ran, and applies each one to the State using that field's **reducer**.

```
Node A returns: {"messages": [msg1], "foo": "a"}
Node B returns: {"messages": [msg2]}         ← parallel in same super-step

After merging (using add_messages reducer on messages):
State = {
  "messages": [msg1, msg2],   ← both appended by the reducer
  "foo": "a"                  ← from node A, default overwrite reducer
}
```

Without a reducer, if two parallel nodes both update `messages`, the last one to finish would **overwrite** the other. The `add_messages` reducer makes merging safe by combining both.

#### Merging in the Tool Loop

This is why `add_messages` is essential in the chatbot → tools → chatbot loop:

```
chatbot node → returns {"messages": [AIMessage with tool_calls]}
                              ↓ (super-step ends, state merges)
tools node   → returns {"messages": [ToolMessage with result]}
                              ↓ (super-step ends, state merges)
chatbot node → now sees full history in state["messages"]
```

Each arrow is one super-step. Messages **accumulate** because `add_messages` appends — they are never overwritten.

#### What "Within One Invoke" Means

All super-step merging happens **inside a single call to `graph.invoke()`**. The entire exchange — including multiple tool calls, evaluator loops, retries — is one invoke. State builds up as super-steps chain together within it.

---

### 3. What Is Cross-Invoke Memory?

**Cross-invoke memory** is the ability to **remember State from a previous `invoke()` call** and pick up where you left off in the *next* call.

By default, without a checkpointer, every `graph.invoke()` starts with a blank slate:

```python
# No checkpointer — stateless, no memory
invoke({"messages": [HumanMessage("Hi, I'm Martin")]})
# State lives, graph runs, State is discarded

invoke({"messages": [HumanMessage("What's my name?")]})
# Brand new State — has no memory of "Martin"
```

With a **checkpointer** and a **`thread_id`**, LangGraph saves the State after every super-step. On the next `invoke()`, it loads the last saved State for that thread and resumes from it:

```python
config = {"configurable": {"thread_id": "martin-session"}}

# First invoke — State is created and saved by the checkpointer
graph.invoke({"messages": [HumanMessage("Hi, I'm Martin")]}, config)
# Checkpointer saves: { messages: [HumanMessage, AIMessage] }

# Second invoke — checkpointer reloads previous State, then appends new input
graph.invoke({"messages": [HumanMessage("What's my name?")]}, config)
# State is now: { messages: [HumanMessage("Hi I'm Martin"), AIMessage(...),
#                             HumanMessage("What's my name?"), AIMessage("You're Martin!")] }
```

The `add_messages` reducer is what makes this seamless — the new human message gets **appended** to the history loaded from the checkpoint, not replacing it.

---

### How All Three Relate — The Full Picture

```
invoke() #1                          invoke() #2
│                                    │
│  super-step 1                      │  super-step 1
│  ├─ chatbot runs                   │  ├─ chatbot runs (sees full history)
│  └─ state merges (add_messages)    │  └─ state merges
│                                    │
│  super-step 2                      │  ...
│  ├─ tools runs                     │
│  └─ state merges                   │
│                                    │
│  super-step 3                      │
│  └─ chatbot runs                   │
│                                    │
└─ checkpointer saves final State ───┘──► checkpointer restores State here
         (cross-invoke memory)
```

| Concept | Scope | Mechanism |
|---|---|---|
| **Super-step** | Single tick within one invoke | Pregel-style parallel execution rounds |
| **Super-step state merging** | Within one invoke | Reducers applied to node outputs after each tick |
| **Cross-invoke memory** | Across multiple invokes | Checkpointer saves/restores State by `thread_id` |

In the labs: Lab 2 introduced all three — `add_messages` handles intra-invoke merging, and `MemorySaver`/`SqliteSaver` with `thread_id` provides cross-invoke memory.
