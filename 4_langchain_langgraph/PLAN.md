# Week 4: LangChain & LangGraph

The new Week 4 of the AI Engineer Agentic track, replacing the old LangGraph-only version
(preserved in `old_4_langgraph/`). This version tells the whole LangChain / LangGraph story
as a **stack of four abstraction layers**, from the raw building blocks up to a full agent harness.

---

## The Big Idea: a Stack, not a Ladder

LangChain / LangGraph is best understood as four layers, where each layer is **built on the one below**.
The spine of the week is a **control - convenience spectrum**: as you climb, you hand more decisions to
the framework in exchange for writing less code.

| Layer | Package (one pip install per layer) | What it gives you | You control... |
|---|---|---|---|
| **1. Building blocks** | `langchain-core` + `langchain-openai` | chat models, the `@tool` decorator, messages, structured output | everything, including the tool-call loop by hand |
| **2. Orchestration** | `langgraph` | `StateGraph`, nodes, conditional edges, checkpointing, durability | the control flow (you design the graph) |
| **3. Agent abstraction** | `langchain` (`create_agent`) | the standard agent loop, prebuilt; tools, memory, structured output, **middleware** | just model + tools + prompt (it builds the graph for you) |
| **4. Agent harness** | `deepagents` (`create_deep_agent`) | an opinionated harness: planning, sub-agents, virtual filesystem | your intent (it brings the architecture) |

**Two framing points to make explicit to students:**

1. **Save the dependency stack for the reveal.** `create_agent` (L3) is itself a LangGraph graph (L2) under the
   hood, and `deepagents` (L4) is built on `create_agent` (L3). The reveal in Day 3 is that the agent is the
   same graph students hand-wrote in Day 2. We build bottom-up so that moment can land, and because students
   arrive from Week 2 (OpenAI Agents SDK) already knowing what a Layer-3 agent feels like. What they are missing
   is the runtime mental model underneath it.

2. **It's a stack you tap at any altitude, not a ladder you climb and abandon.** Real apps mix layers - use
   `create_agent` (L3) but drop to `langgraph` (L2) for a custom multi-agent flow, or reach for an L1 building
   block for a one-off call. **Day 5's Sidekick is the synthesis**: `create_agent` (L3) wrapped in your *own*
   hand-written loop - deliberately picking your altitude.

> Note on naming: "LangChain" spans Layers 1 and 3 (both the core building blocks and `create_agent` ship under
> the langchain umbrella), while `langgraph` sits *between* them as a separate package. The per-layer package
> table above is the clean way to present this so students aren't confused.

---

## Conventions (apply to every notebook)

Follow the style of `2_openai/` and `1_foundations/`:

- **First code cell**: ALL imports plus `load_dotenv(override=True)` together. Nothing else scattered later.
- **Explain in Markdown cells, not in comments**: carry the teaching in a brief markdown cell before each step,
  all the way through, like an interactive book. Keep code comments sparing.
- **HTML callout segments** for the set-piece moments, following the `1_foundations/` examples: the orange
  STOP / "Are you ready" warnings, the blue "live resource" / docs notes, the business-application asides, and
  the exercise prompts. These are `<table>` blocks with the shared assets `stop.png`, `tools.png`,
  `exercise.png`, `thanks.png`. Friendly, encouraging tone with the occasional playful hook.
- **Latest models**: `gpt-5.4-nano` (cheapest), `gpt-5.4-mini` (default workhorse), `gpt-5.5` (the powerful one,
  when a lab wants more capability). Use `ChatOpenAI(model=...)` from `langchain-openai`. Show OpenRouter too for
  the multi-provider point.
- **Modern idioms only**: use the `@tool` decorator from `langchain_core.tools`, never the legacy
  `langchain.agents.Tool(...)` wrapper from the old labs.
- End each notebook with an Exercise callout.

### Student-facing writing style

Watch for the LLM-generated tells that readers find off-putting, and avoid them in all markdown that students read:

- Do not use the "it's not X, it's Y" / "not the premise, the punchline" antithesis construct.
- Do not write in short staccato fragments. Let sentences breathe and connect naturally.
- Do not use em-dashes. Use commas, parentheses, or separate sentences instead.
- Write the way a friendly human instructor talks: plain, warm, and direct.

### Running and verifying notebooks

Notebooks can be authored and executed end to end, and Ed is happy for verification runs to hit live services.

- Default model for labs is `gpt-5.4-mini`, which is totally fine to run against freely.
- For the OpenRouter multi-provider demos, any modern model at a similar price point works, for example
  `google/gemini-3.1-flash-lite` or `anthropic/claude-haiku-4.5`. Pick from whichever provider suits the lesson.
- Headful Playwright opening a real browser window on Ed's machine is fine, as is sending Pushover notifications
  as often as needed. Verification runs are real runs (live API calls, real browser, real notifications), and
  that is acceptable here.
- Execution tooling is installed: `nbconvert` and `nbclient` (dev deps). Run a notebook headless with
  `uv run jupyter nbconvert --to notebook --execute <nb>.ipynb` to execute every cell and capture outputs back
  into the file. The notebook kernelspec should point at the project `.venv`.

## Dependencies (installed)

All installed into the single shared project venv (resolved cleanly alongside openai-agents / litellm):

```
langchain            # Layer 3: create_agent      (1.3.4)
langgraph            # Layer 2: StateGraph, edges  (1.2.4)
langgraph-checkpoint-sqlite  # Day 2: SQLite checkpointing  (3.1.0)
langchain-openai     # Layer 1: ChatOpenAI         (1.2.2)
langchain-community  # utilities: Serper wrapper, Wikipedia (used sparingly)  (0.4.2)
langchain-mcp-adapters  # load MCP servers as LangChain tools  (0.2.2)
deepagents           # Layer 4: create_deep_agent  (0.6.8)
```

Dev deps for executing notebooks: `nbconvert` (7.17.1), `nbclient` (0.11.0). `mcp` and `gradio>=6.14` were
already present. Legacy APIs live in `langchain-classic` (avoid).

---

## Day 1 - The Four Layers + Layer 1 hands-on

**Teach**: the stack-not-a-ladder framing (the table above), the control-convenience spine, and the per-layer
package map. Set expectations for the whole week.

**Lab 1** - Layer 1 building blocks:
- `ChatOpenAI` as a unified model interface - "a heavyweight LiteLLM": not just a model call, but models +
  `@tool` + messages + structured output as one consistent set of LEGO bricks.
- A call to OpenAI, then the same against **OpenRouter** (base_url swap) to make the multi-provider point.
- Define a tool with the `@tool` decorator; show `.invoke()`, the auto-generated schema, and `bind_tools`.
- Show that at Layer 1 *you* would have to write the tool-calling loop by hand - which motivates Layer 2.

## Day 2 - Layer 2: LangGraph

**Teach**: State (with reducers / `add_messages`), the Graph, nodes, conditional edges, super-steps, and why
checkpointing - not the reducer - is what gives you memory *between* invocations.

**Lab 2** - a tight, modern condensation of `old_4_langgraph/1_lab1.ipynb` + `2_lab2.ipynb`:
- Build a graph with no LLM (functions only) to prove "LangGraph is just Python functions", then again with an LLM.
- Add tools (`@tool` decorator + `ToolNode` + `tools_condition`), conditional edges, the tool loop.
- **LangSmith** for observability (smith.langchain.com) - introduced once here, reused everywhere after.
- Memory: `MemorySaver`, then **SQLite checkpointing**; show `get_state` / `get_state_history` / time-travel.
- A small Gradio `ChatInterface` to make it tangible.

## Day 3 - Layer 3: create_agent

**Teach**: `create_agent` returns a compiled LangGraph graph - peel it back to reveal the Day-2 graph (the reveal).

**Lab 3** - ONE comprehensive notebook, organized into clear **Parts** (it's dense, so pace it):
- **Part 1**: the simplest `create_agent` (model + prompt), an instant agent set against Day 2's hand-wiring.
  Then render its underlying graph with `agent.get_graph().draw_mermaid_png()` to show it is the same LangGraph
  shape we built by hand in Day 2. This is the visual payoff for the whole week (verified: `create_agent`
  returns a `CompiledStateGraph`, so the same `draw_mermaid_png()` from Day 2 works unchanged).
- **Part 2**: tools - hand it `@tool` functions; show the loop it runs for you.
- **Part 3**: memory - the checkpointer, thread_id, multi-turn.
- **Part 4**: structured output - `response_format` with a Pydantic schema.
- **Part 5**: **middleware** (the headline new feature of LangChain 1.0) - `before_model` / `after_model` /
  `wrap_tool_call` for guardrails, summarization, logging. Seed it here so Day 5 can use it for human-in-the-loop.
- **Part 6**: an **MCP server** as tools via `langchain-mcp-adapters` - including **headful Playwright** so the
  agent visibly drives a browser and searches for something (see Playwright note below).

## Day 4 - Layer 4: Deep Agents

**Teach**: when create_agent isn't enough - deepagents brings an opinionated harness (planning tool, sub-agents,
virtual filesystem) so you supply intent and it supplies the architecture.

**Lab 4** - a short, elegant `create_deep_agent` demo, ideally also driving headful Playwright, on a task that
shows off planning + filesystem producing a tangible artifact (task chosen from the survey below).

## Day 5 - The Sidekick (the synthesis)

**Teach**: pick your altitude. The worker becomes a one-line `create_agent` (L3), but *you* hand-code the loop
around it - the inversion of the old raw-LangGraph Sidekick. Human-in-the-loop done the modern way via middleware.

Delivered as `.py` modules + `app.py` + a Gradio UI (request + success-criteria textboxes, Reset / Go), carrying
over the best of the old Sidekick. Tools: a mix of MCP servers (headful Playwright; the filesystem/sandbox
reference server for reading/writing a sandbox dir) and `@tool` LangChain tools (Serper search, Pushover push,
Python, etc.).

**Build it BOTH ways so Ed can judge the feel** (and drop the heavier one if it's too much):
- **(A) With the evaluator loop**: worker `create_agent` + a homemade evaluator/retry loop driven by
  success-criteria and structured `EvaluatorOutput`, plus human-in-the-loop. (Closest to the old Sidekick.)
- **(B) Without the evaluator**: a single `create_agent` with a homemade loop just for human interaction -
  simpler, leaner.

---

## Playwright MCP - ensuring HEADFUL

We use Microsoft's `@playwright/mcp` (loaded via `langchain-mcp-adapters`) so the browser is **visible**.

- Its default *is* headed; there is **no `--headed` flag** (headed is the default, `--headless` turns it off).
- Ed has seen it come up headless in practice - almost certainly because a client injected `--headless`. Since
  **we** spawn it (stdio transport, we own the args), we force headed two ways for certainty:
  - omit `--headless`, AND
  - pass `--config config.json` with `{ "browser": { "launchOptions": { "headless": false } } }`
  - (and ensure the env var `PLAYWRIGHT_MCP_HEADLESS` is not set true).
- **Gotcha for a `stop.png` callout**: on macOS, headed mode genuinely grabs the cursor/foreground while it
  drives the browser (it can hijack the OS cursor). Warn students.

---

## Tools inventory & task design (TO DO before Days 4-5)

Chicken-and-egg: survey what's *readily available and reliably impressive* first, then reverse-engineer 3-4
tangible, useful Sidekick / Deep Agent tasks with great visible outcomes. Candidate tools:

- **Serper.dev web search** - account already set up, key in `SERPER_API_KEY`. Strong default. Wrap via `@tool`
  (or `langchain_community.utilities.GoogleSerperAPIWrapper`).
- **Playwright MCP (headful)** - visible browsing, navigation, extraction, screenshots.
- **Filesystem / sandbox MCP server** - read/write a sandbox dir (the Anthropic reference server).
- **Pushover push** - `PUSHOVER_TOKEN` / `PUSHOVER_USER` already set.
- **Python REPL**, **Wikipedia** - from the old labs.
- **Deep Agents built-ins** - planning tool, sub-agents, virtual filesystem.

Run a read-only survey of these, confirm which combinations are robust and visually compelling, then draft the
concrete task list here.

---

## Housekeeping

- `old_4_langgraph/` holds the previous version for reference.
- `4_langchain_langgraph/community_contributions/` carries over older entries - intentionally left as-is.

---

# LangChain 1.x Reference (idiomatic, latest)

> The following sections are the authoritative reference for how we write code this week. Every signature,
> import path, and snippet below was **verified by introspection and execution against the installed versions**
> (not just docs - LangChain docs blend legacy 0.x material, so we ground-truthed everything).
>
> **Verified against:** `langchain` 1.3.4, `langchain-core` 1.4.2, `langgraph` 1.2.4,
> `langgraph-checkpoint` 4.1.1, `langgraph-checkpoint-sqlite` 3.1.0, `langgraph-prebuilt` 1.1.0,
> `langchain-openai` 1.2.2, `langchain-community` 0.4.2, `langchain-mcp-adapters` 0.2.2, `mcp` 1.27.0,
> `deepagents` 0.6.8, `langsmith` 0.8.11, `pydantic` 2.13.3.
>
> **Legacy lives in `langchain-classic`** - if you ever reach for `LLMChain`, `initialize_agent`,
> `AgentExecutor`, `ConversationChain`, or the old `langchain.agents.Tool(...)` wrapper, STOP: you're in
> legacy territory. None of those appear below by design.

---

## Layer 1 Reference: Building Blocks (langchain-core, langchain-openai)

Note on imports: the new 1.x docs often show `from langchain.messages` / `from langchain.tools`, but the
underlying canonical path is `langchain_core.*`. Both work; this reference uses `langchain_core.*`.

### 1. Chat model: `ChatOpenAI`

Instantiate with `model` and `temperature`, then call `.invoke()` for a single response, `.stream()` for token
chunks, `.batch()` for a list of inputs - each with an `a`-prefixed async twin (`ainvoke`, `astream`, `abatch`).
Point `base_url` at any OpenAI-compatible endpoint (e.g. OpenRouter) and it just works.

```python
import os
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-5.4-mini", temperature=0.7)

resp = model.invoke("Why is the sky blue?")
print(resp.content)            # str; resp.text also returns the text

for chunk in model.stream("Tell me a joke"):
    print(chunk.content, end="", flush=True)

results = model.batch(["Capital of France?", "Capital of Japan?"])

# Async
resp = await model.ainvoke("Hello")
async for chunk in model.astream("Stream this"):
    print(chunk.content, end="")

# OpenRouter (OpenAI-compatible) - base_url + api_key are the constructor kwargs
or_model = ChatOpenAI(
    model="moonshotai/kimi-k2.6",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    temperature=0,
)
```

- Gotcha: `.invoke()` returns an `AIMessage`; use `.content` (or `.text`) for the string. `.text` is an
  attribute, not a method - do not call `.text()`.
- Legacy trap: do NOT use the completion-style `OpenAI` class or `LLMChain`. Instantiate `ChatOpenAI` and call it.

### 2. Messages

Four current message types live in `langchain_core.messages`. You can pass either message objects or plain
OpenAI-style role dicts - both are accepted. A bare string is shorthand for a single `HumanMessage`.

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

messages = [
    SystemMessage("You are a concise assistant."),
    HumanMessage("Summarize photosynthesis in one line."),
]
resp = model.invoke(messages)        # -> AIMessage

# Plain dicts (OpenAI style) - equivalent
resp = model.invoke([
    {"role": "system", "content": "You are a concise assistant."},
    {"role": "user", "content": "Summarize photosynthesis in one line."},
])
```

- `ToolMessage` carries a tool result back to the model and requires `tool_call_id` (see the loop in section 4).
- Legacy trap: the old `langchain.schema` import path is gone - use `langchain_core.messages`.

### 3. Tools: the `@tool` decorator

Decorate a typed function with `@tool` from `langchain_core.tools`. The docstring becomes the model-facing
description; type hints become the args schema automatically. Call a tool directly with `.invoke({...})`.

```python
from langchain_core.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b

add.name          # 'add'
add.description   # 'Add two numbers and return the result.'
add.args          # {'a': {...}, 'b': {...}}
add.invoke({"a": 2, "b": 3})   # -> 5
```

For richer schemas (descriptions, defaults, validation), pass a Pydantic model via `args_schema`:

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class WeatherInput(BaseModel):
    location: str = Field(description="City name")
    units: str = Field(default="celsius", description="Temperature unit")

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius") -> str:
    """Get the current weather for a location."""
    return f"22 degrees {units}"
```

- Legacy trap: do NOT use `from langchain.agents import Tool` / `Tool(name=..., func=...)`. The `@tool`
  decorator (or a `BaseTool` subclass) is the only current idiom.

### 4. Binding tools and the hand-run tool loop

`model.bind_tools([...])` returns a model that advertises the tools. The response is an `AIMessage` whose
`.tool_calls` is a list of dicts with `name`, `args`, `id`, `type`. At Layer 1 you run the loop yourself -
this manual plumbing is exactly what Layers 2/3 automate.

```python
from langchain_core.messages import HumanMessage, ToolMessage

tools = [add]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)

messages = [HumanMessage("What is 2 + 3?")]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

for call in ai_msg.tool_calls:    # [{'name':'add','args':{'a':2,'b':3},'id':'call_1','type':'tool_call'}]
    result = tools_by_name[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

final = model_with_tools.invoke(messages)   # model now sees the tool result
print(final.content)
```

- Gotcha: every `ToolMessage` must echo the originating `tool_call_id`, and the `AIMessage` containing the
  tool calls must remain in history before the `ToolMessage`s.

### 5. Structured output

`model.with_structured_output(PydanticModel)` returns a runnable whose `.invoke()` yields a populated, validated
instance (not an `AIMessage`). Defaults to `method="json_schema"`.

```python
from pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(description="The title of the movie")
    year: int = Field(description="Release year")
    rating: float = Field(description="Rating out of 10")

structured = model.with_structured_output(Movie)
movie = structured.invoke("Give details about the movie Inception")   # -> Movie instance
```

- Pass `include_raw=True` to also get the raw `AIMessage` (dict with `parsed`, `raw`, `parsing_error`).
- Legacy trap: do NOT chain `prompt | model | parser` for this - `with_structured_output` is the current idiom.

**Docs:**
- https://docs.langchain.com/oss/python/langchain/models
- https://docs.langchain.com/oss/python/langchain/messages
- https://docs.langchain.com/oss/python/langchain/tools
- https://docs.langchain.com/oss/python/langchain/models#structured-outputs
- https://reference.langchain.com/python/

---

## Layer 2 Reference: LangGraph Orchestration

### 1. Defining State + reducers

State is a `TypedDict`; each key updates independently. By default a node's returned value **overwrites** the
key. A **reducer** is a function `(current, update) -> new` attached via `Annotated[type, reducer]` that defines
how updates combine instead. Use a plain value for "latest single value" (counter, flag, current question); use
a reducer to accumulate. `add_messages` is the canonical chat-history reducer (appends, merging by message ID).

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages   # also re-exported from langgraph.graph

class State(TypedDict):
    messages: Annotated[list, add_messages]   # reducer: appends/merges
    question: str                             # plain: overwritten each update
```

Shortcut: `from langgraph.graph import MessagesState` already has `messages: Annotated[list, add_messages]`;
subclass it to add fields.

- Gotcha: the reducer governs accumulation *within a single run*, not memory across runs (that's checkpointing).

### 2. Building a graph

```python
from langgraph.graph import StateGraph, START, END

def chatbot(state: State) -> dict:
    return {"messages": [...]}   # return only the keys you want to update

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile()        # MUST compile before use
```

**`add_conditional_edges(source, path, path_map=None)`**: `path` is a function taking state and returning the
next node name(s) (or a hashable key); optional `path_map` maps keys to node names (use it when routing returns
booleans/enums, and it makes edges render correctly in the diagram).

```python
def route(state: State) -> str:
    return "tools" if needs_tool(state) else END

builder.add_conditional_edges("chatbot", route)                        # returns node names directly
builder.add_conditional_edges("chatbot", route, {True: "tools", False: END})  # with mapping
```

- Gotcha: nodes return partial dicts (only changed keys). `START`/`END` are sentinels, not strings.
  `.compile()` is mandatory and returns a `CompiledStateGraph`.

### 3. Tool-calling graph (ToolNode + tools_condition)

`ToolNode` and `tools_condition` come from `langgraph.prebuilt`. Bind tools inside the node. `tools_condition`
returns `"tools"` if the last AI message has tool calls, else `"__end__"` - pass it directly as the `path`.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]

tools = [...]
llm = ChatOpenAI(model="gpt-5.4-mini").bind_tools(tools)

def chatbot(state: State) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))            # name "tools" matches tools_condition's return
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)   # -> "tools" or END
builder.add_edge("tools", "chatbot")                  # loop back so the model sees tool results
graph = builder.compile()
```

- Gotcha: the tools node must be named `"tools"`. The `tools -> chatbot` edge closes the loop; omit it and the
  run ends after one tool call. (`langgraph.prebuilt.create_react_agent` is the OLD prebuilt agent - superseded
  by `create_agent`; not used.)

### 4. Memory / checkpointing

The reducer accumulates state *within one run*. **Memory between separate `invoke` calls comes from a
checkpointer**, which persists a snapshot at every **super-step** keyed by `thread_id`. On the next `invoke`
with the same `thread_id`, saved state is loaded and merged via reducers - so chat history carries over.

```python
from langgraph.checkpoint.memory import MemorySaver        # in-memory (dev); alias of InMemorySaver
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-123"}}
graph.invoke({"messages": [{"role": "user", "content": "Hi, I'm Ed"}]}, config)
graph.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, config)  # answers "Ed"
```

**SQLite** (`from_conn_string` is a context manager):

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(inputs, {"configurable": {"thread_id": "user-123"}})
# To hold it open long-term, construct directly:
#   import sqlite3; SqliteSaver(sqlite3.connect("checkpoints.sqlite", check_same_thread=False))
```

**Async SQLite** (use with `ainvoke`/`astream`):

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    await graph.ainvoke(inputs, config)
```

- Gotcha: `thread_id` is required once a checkpointer is attached. `from_conn_string` yields a saver only inside
  the `with` block - compile and invoke inside it.

### 5. Inspecting state & time travel

```python
config = {"configurable": {"thread_id": "user-123"}}

snapshot = graph.get_state(config)        # StateSnapshot for the latest checkpoint
snapshot.values["messages"]               # the persisted state
snapshot.next                             # node(s) queued next (() if done)

history = list(graph.get_state_history(config))   # newest -> oldest, one per super-step
checkpoint_id = history[2].config["configurable"]["checkpoint_id"]

# Time travel: resume/replay from an earlier checkpoint
resume_config = {"configurable": {"thread_id": "user-123", "checkpoint_id": checkpoint_id}}
graph.invoke(None, resume_config)         # None continues from the checkpoint as-is
```

- Gotcha: history is most-recent-first; `checkpoint_id` lives under `snapshot.config["configurable"]`.

### 6. Streaming & async

- `invoke` vs `ainvoke`: sync vs async; both return the final state dict.
- `stream` vs `astream`: incremental chunks, controlled by `stream_mode`:
  - `"values"` - full state after each super-step (default for invoke)
  - `"updates"` - only the delta each node emitted (`{node: update}`) - best for logging
  - `"messages"` - LLM tokens as `(chunk, metadata)` tuples - for token-by-token UIs

```python
for chunk in graph.stream(inputs, config, stream_mode="updates"):
    print(chunk)            # {"chatbot": {"messages": [...]}}

async for token, meta in graph.astream(inputs, config, stream_mode="messages"):
    print(token.content, end="")
```

### 7. Visualizing

```python
from IPython.display import Image, display
display(Image(graph.get_graph().draw_mermaid_png()))   # renders via mermaid.ink (needs network)
# graph.get_graph().draw_mermaid()  # offline Mermaid source text
```

**Docs:**
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/streaming
- https://reference.langchain.com/python/langgraph/

---

## Layer 3 Reference: create_agent

`create_agent` is LangChain 1.x's standard agent constructor (`langchain.agents`). It **supersedes**
`langgraph.prebuilt.create_react_agent` and the legacy `AgentExecutor`/`initialize_agent`. It returns a
**compiled LangGraph graph** (`CompiledStateGraph`) - so everything from Layer 2 (`.invoke`/`.ainvoke`/`.stream`,
`config`, checkpointers, `thread_id`) applies directly, and the agent is itself a graph node you can compose.

### Inspected signature (real, from `inspect.signature`)

```python
from langchain.agents import create_agent

create_agent(
    model: str | BaseChatModel,
    tools: Sequence[BaseTool | Callable | dict] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    response_format: ResponseFormat | type | dict | None = None,
    state_schema: type[AgentState] | None = None,
    context_schema: type | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    interrupt_before: list[str] | None = None,
    interrupt_after: list[str] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
    transformers: Sequence[TransformerFactory] | None = None,
) -> CompiledStateGraph
```

### 1. Simplest agent: model + system prompt

`model` accepts a **provider-prefixed string** (`"openai:gpt-5.4-mini"`, resolved via `init_chat_model`) or a
**chat model instance**. The system-prompt param is `system_prompt` (verified - NOT `prompt`, NOT the legacy
`state_modifier`); it is keyword-only.

```python
from langchain.agents import create_agent

agent = create_agent(model="openai:gpt-5.4-mini", system_prompt="You are a concise assistant.")

# Or a configured instance:
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0)
agent = create_agent(model=llm, system_prompt="You are a concise assistant.")
```

### 2. Tools + 3. Invoking + reading results

```python
from langchain_core.tools import tool
from langchain.agents import create_agent

@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"It's sunny in {city}."

agent = create_agent(model="openai:gpt-5.4-mini", tools=[get_weather],
                     system_prompt="You are a weather assistant.")

result = agent.invoke({"messages": [{"role": "user", "content": "Weather in Paris?"}]})
print(result["messages"][-1].content)
# Async: await agent.ainvoke({"messages": [...]})

# Streaming
for chunk in agent.stream({"messages": [{"role": "user", "content": "Weather in Paris?"}]},
                          stream_mode="values"):
    chunk["messages"][-1].pretty_print()
```

### 4. Memory (checkpointer + thread_id)

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model="openai:gpt-5.4-mini", tools=[get_weather], checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "user-123"}}
agent.invoke({"messages": [{"role": "user", "content": "I'm in Paris."}]}, config=config)
agent.invoke({"messages": [{"role": "user", "content": "What's the weather here?"}]}, config=config)
```

- Gotcha: `checkpointer` persists one thread (chat memory); `store=` is the separate cross-thread parameter.

### 5. Structured output

Use `response_format=` with a Pydantic model. The parsed object is returned under the **`structured_response`**
key (verified - `AgentState` keys are `messages`, `jump_to`, `structured_response`), NOT in the last message.

```python
from pydantic import BaseModel
from langchain.agents import create_agent

class WeatherReport(BaseModel):
    city: str
    summary: str
    temp_c: float

agent = create_agent(model="openai:gpt-5.4-mini", tools=[get_weather], response_format=WeatherReport)
result = agent.invoke({"messages": [{"role": "user", "content": "Weather in Paris?"}]})
report = result["structured_response"]   # WeatherReport instance
```

- Gotcha: a bare Pydantic class is auto-wrapped; for explicit control pass a `ToolStrategy`/`ProviderStrategy`.

### 6. Middleware

`create_agent` exposes `middleware=` (a `Sequence[AgentMiddleware]`) - the primary extensibility mechanism in 1.x
(summarization, guardrails, human-in-the-loop). See the dedicated middleware section below.

**Docs:**
- https://docs.langchain.com/oss/python/langchain/agents
- https://reference.langchain.com/python/langchain/agents/factory/create_agent
- https://docs.langchain.com/oss/python/langchain/structured-output
- https://docs.langchain.com/oss/python/langchain/middleware

---

## Reference: Agent Middleware & Human-in-the-Loop

### 1. What middleware is

Middleware injects behavior at fixed points around the agent's reason->act loop without rewriting it. Verified
hook points on the `AgentMiddleware` base class (each has an async twin `a...`):

| Hook | When it runs |
|------|--------------|
| `before_agent` / `after_agent` | Once, at the very start/end of the agent run |
| `before_model` | Before each model call (mutate state, short-circuit) |
| `after_model` | After each model call (inspect/modify the AIMessage) |
| `wrap_model_call` | **Wraps** the model call - call `handler(request)` yourself; retry, swap models, edit request/response |
| `wrap_tool_call` | **Wraps** each tool execution - intercept/short-circuit |

```python
before_model(self, state, runtime) -> dict | None          # return a state update or None
wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse | AIMessage
wrap_tool_call(self, request: ToolCallRequest, handler) -> ToolMessage | Command
```

### 2. Attaching

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, PIIMiddleware

agent = create_agent(
    model="gpt-5.5", tools=[...],
    middleware=[SummarizationMiddleware(model="gpt-5.4-mini"), PIIMiddleware("email")],
)
```

- Order matters: middleware wrap in list order (first = outermost). `middleware=` is keyword-only.

### 3. Built-in middleware (the REAL classes shipping in 1.3.4)

All importable from `langchain.agents.middleware`:

| Class | Purpose |
|-------|---------|
| `SummarizationMiddleware` | Summarizes history when token limits are approached |
| `HumanInTheLoopMiddleware` | Pauses for human approve/edit/reject/respond on selected tool calls |
| `PIIMiddleware` | Detects/redacts/masks/hashes/blocks PII (email, credit_card, ip, mac_address, url, custom) |
| `ModelFallbackMiddleware` | Fallback to alternative models on error |
| `ModelRetryMiddleware` / `ToolRetryMiddleware` | Retry failed model/tool calls with backoff |
| `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` | Cap number of model/tool calls |
| `LLMToolSelectorMiddleware` | LLM pre-selects relevant tools before the main call |
| `LLMToolEmulator` | Emulates tools with an LLM instead of executing (testing) |
| `ContextEditingMiddleware` | Prunes/edits tool results to manage context (`ClearToolUsesEdit`) |
| `TodoListMiddleware` | Gives the agent todo-list management tools |
| `ShellToolMiddleware` | Persistent shell tool (Docker/Host/Codex execution policies) |
| `FilesystemFileSearchMiddleware` | Glob/Grep search over the filesystem |

Helpers: `AgentMiddleware` (base), `ModelRequest`/`ModelResponse`/`ToolCallRequest`, `RedactionRule`,
`InterruptOnConfig`, `PIIDetectionError`.

```python
from langchain.agents.middleware import SummarizationMiddleware

SummarizationMiddleware(
    model="gpt-5.4-mini",
    trigger=("fraction", 0.8),   # also ("tokens", N) or ("messages", N)
    keep=("messages", 20),
)
```

### 4. Writing custom middleware

```python
# (a) Subclass
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

class LoggingMiddleware(AgentMiddleware):
    def before_model(self, state, runtime) -> dict | None:
        print("messages so far:", len(state["messages"]))
        return None
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        response = handler(request)          # YOU call the model
        print("model responded")
        return response

# (b) Decorators (return a ready-made middleware)
from langchain.agents.middleware import before_model, wrap_tool_call

@before_model
def trim(state, runtime):
    return None

@wrap_tool_call
def guard(request, handler):
    return handler(request)
```

Verified decorators: `before_agent`, `after_agent`, `before_model`, `after_model`, `wrap_model_call`,
`wrap_tool_call`, `dynamic_prompt`, `hook_config`. Pass an instance or a decorated function into `middleware=[...]`.

### 5. Human-in-the-loop (for the Sidekick)

Both approaches require a **checkpointer** and a **`thread_id`**. Prefer the built-in middleware for tool-approval
gating; drop to raw `interrupt()` for a custom pause inside your own tool/middleware.

```python
# Built-in HITL middleware
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

agent = create_agent(
    model="gpt-5.5", tools=[send_email, delete_file],
    middleware=[HumanInTheLoopMiddleware(interrupt_on={
        "send_email": True,                                   # all decisions allowed
        "delete_file": {"allowed_decisions": ["approve", "reject"]},
    })],
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "sidekick-1"}}
result = agent.invoke({"messages": [{"role": "user", "content": "email the team"}]}, config)
# result["__interrupt__"] holds the pending tool call(s). Ask the human, then resume:
agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)
# decision types: approve | {"type":"edit","args":{...}} | reject | {"type":"respond","message":"..."}
```

```python
# Raw LangGraph interrupt (custom pause, e.g. inside a tool)
from langgraph.types import interrupt, Command   # NOTE: langgraph.types, not langchain

def ask_human(question: str) -> str:
    """Ask the user a clarifying question."""
    answer = interrupt({"question": question})   # pauses the graph here
    return answer

agent.invoke(Command(resume="the user's typed answer"), config)   # resume with the value
```

- Gotchas: no checkpointer => no pause/resume. The two resume shapes differ: HITL middleware expects
  `Command(resume={"decisions": [...]})`; a bare `interrupt(...)` expects `Command(resume=<value>)`. The `wrap_*`
  hooks MUST call `handler(...)` or they silently skip the model/tool.

**Docs:**
- https://docs.langchain.com/oss/python/langchain/middleware
- https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- https://reference.langchain.com/python/langchain/middleware/

---

## Reference: MCP Servers as Tools (incl. headful Playwright + filesystem)

**Verified API:** `from langchain_mcp_adapters.client import MultiServerMCPClient`. `client.get_tools()` is
**async** (must `await`). `client.session(server_name)` is an async context manager for stateful use. Constructor
takes one `connections` dict. Transport keys: `"stdio"` and `"streamable_http"` (not `"http"`).

### 1. MultiServerMCPClient - connections dict

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "filesystem": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/abs/sandbox/dir"],
    },
    "weather": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/mcp",
        # "headers": {"Authorization": "Bearer ..."},  # optional
    },
})
```

### 2. Loading tools into create_agent

Tools are **async**, so drive the agent with `ainvoke` (not `invoke`).

```python
from langchain.agents import create_agent

tools = await client.get_tools()                 # async - must await
agent = create_agent("openai:gpt-5.4-mini", tools=tools)
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "List the files in the sandbox."}]}
)
```

### 3. Playwright MCP (`@playwright/mcp`), HEADFUL

Default is headed; there is **no `--headed` flag** (`--headless` turns it OFF). To GUARANTEE headed even if a
client injects `--headless`, pass a config file and the env belt-and-suspenders.

`playwright-config.json`:
```json
{ "browser": { "launchOptions": { "headless": false } } }
```

```python
"playwright": {
    "transport": "stdio",
    "command": "npx",
    "args": ["@playwright/mcp@latest", "--config", "/abs/playwright-config.json"],
    "env": {"PLAYWRIGHT_MCP_HEADLESS": "false"},
},
```

Main tools: `browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot` (accessibility-tree, the
primary "see the page" tool), `browser_take_screenshot`, `browser_fill_form`, `browser_press_key`,
`browser_hover`, `browser_select_option`, `browser_wait_for`, `browser_navigate_back`, `browser_tabs`,
`browser_resize`, `browser_close`.

- Gotcha (macOS): in headed mode the browser window grabs focus and can **hijack the cursor** while the agent
  drives clicks. Use a separate desktop/Space; or run headless for unattended/CI runs.

### 4. Filesystem MCP (`@modelcontextprotocol/server-filesystem`)

Trailing positional args are the **allowed sandbox directories** (absolute paths); access outside is refused.

```python
"filesystem": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/abs/sandbox/dir"],
},
```

Tools: `read_text_file`, `read_media_file`, `read_multiple_files`, `write_file`, `edit_file`,
`create_directory`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `move_file`,
`search_files`, `get_file_info`, `list_allowed_directories`. (Note: it's `read_text_file`, NOT `read_file`.)

### 5. Lifecycle

Keep the `client` object alive for the life of the app and reuse the `tools` list (each stdio tool call opens a
fresh stateless session). For a shared live browser/session across calls, use `async with client.session("playwright") as session:`. Prerequisite: **Node.js / `npx`** (first run may download the package + browser binaries).

**Docs:**
- https://docs.langchain.com/oss/python/langchain/mcp
- https://github.com/langchain-ai/langchain-mcp-adapters
- https://github.com/microsoft/playwright-mcp
- https://playwright.dev/mcp/configuration/options
- https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

---

## Layer 4 Reference: Deep Agents (create_deep_agent)

`deepagents` is an opinionated **agent harness** on top of `create_agent`: it adds a **planning tool** (todo
list), a **virtual filesystem** (scratch memory), and **sub-agents** (context isolation), by assembling a
`create_agent` with a fixed middleware stack. A deep agent IS a Layer-3 agent with batteries included - same
`.invoke`/`.ainvoke`/`.stream` interface.

### Inspected signature (real)

```python
from deepagents import create_deep_agent

create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | Callable | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format=None,
    state_schema: type[DeepAgentState] | None = None,
    context_schema=None,
    checkpointer: None | bool | BaseCheckpointSaver = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```

Gotchas:
- The system-prompt param is **`system_prompt`**, NOT `instructions` (the old 0.0.x name is gone in 0.6.8).
- `tools` is **additive** - it merges with the built-in suite (never removes a built-in).
- Always pass a `model` (`model=None`/the default is deprecated since 0.5.3). Accepts a `provider:model` string
  or a `BaseChatModel`. For `openai:` it defaults to the **Responses API**; pass
  `init_chat_model("openai:...", use_responses_api=False)` for chat-completions.
- Answer is `result["messages"][-1].content`.

Exports: `create_deep_agent`, `SubAgent`, `CompiledSubAgent`, `AsyncSubAgent`, `DeepAgentState`,
`FilesystemMiddleware`, `SubAgentMiddleware`, `MemoryMiddleware`, `RubricMiddleware`, `HarnessProfile`,
`ProviderProfile`, `backends`, `middleware`, `profiles`.

### Built-in tools the harness injects
- `write_todos` - the planning/todo tool (decompose, track, revise).
- Filesystem: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`.
- `execute` - shell (only works if the backend implements the sandbox protocol; default backend errors).
- `task` - delegate to a sub-agent.

### Virtual filesystem (state vs real dir)
Files are **virtual / in-state by default** (`StateBackend` - ephemeral, persists within a thread via
checkpointing). Back it with a real directory via `backend`:

```python
from deepagents.backends import FilesystemBackend
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt="You are a coding assistant.",
    backend=FilesystemBackend(root_dir="./workspace"),   # real files (grants direct read/write)
)
```

Backends in `deepagents.backends`: `StateBackend` (default), `FilesystemBackend` (local disk), `StoreBackend`
(cross-thread), `CompositeBackend`, plus `LocalShellBackend`/`LangSmithSandbox` for `execute`.

### Sub-agents
Delegated to via the `task` tool. `SubAgent` is a TypedDict - **required:** `name`, `description`,
`system_prompt`; **optional:** `tools`, `model`, `middleware`, `interrupt_on`, `skills`, `permissions`,
`response_format`. (Instruction key is `system_prompt`, NOT `prompt`. Omitting `tools` inherits parent tools.)

```python
research_subagent = {
    "name": "researcher",
    "description": "Researches a topic in depth and returns a summary.",
    "system_prompt": "You are a thorough researcher. Use the web tools, then summarize.",
    "tools": [web_search],            # optional; inherits parent tools if omitted
    "model": "openai:gpt-5.4-mini",   # optional override
}
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6", tools=[web_search],
    system_prompt="You orchestrate research. Delegate deep digs to the researcher subagent.",
    subagents=[research_subagent],
)
```

### Minimal end-to-end

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[get_weather, get_population],
    system_prompt="You are a helpful city-facts assistant. Plan with the todo tool for multi-part tasks.",
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Compare the weather and population of SF and NYC."}]}
)
print(result["messages"][-1].content)
```

**Docs:**
- https://docs.langchain.com/oss/python/deepagents
- https://docs.langchain.com/oss/python/deepagents/models
- https://github.com/langchain-ai/deepagents

---

## Reference: LangSmith Tracing

### Enabling (env vars - prefer the `LANGSMITH_*` names)

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=week4-langchain     # optional; groups traces
LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # optional; for EU/regional
```

The older `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` still work but are legacy.

### Automatic for LangChain / LangGraph
Once the env vars are set, every LangChain/LangGraph run (incl. `create_agent` and `deepagents`) is traced with
no code change. Dashboard: **https://smith.langchain.com**.

### `@traceable` for arbitrary functions

```python
from langsmith import traceable

@traceable
def fetch_and_summarize(url: str) -> str:
    ...

@traceable(run_type="tool", name="weather_lookup")
def get_weather(city: str) -> str:
    ...
```

Still requires `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY` (otherwise a no-op).

**Docs:**
- https://docs.langchain.com/langsmith/
- https://docs.langchain.com/langsmith/observability-quickstart
- https://docs.smith.langchain.com/
