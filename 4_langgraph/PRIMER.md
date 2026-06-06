# Week 4 Primer — LangGraph: Agents as Explicit State Machines

> Read before the labs. CrewAI hid the orchestration behind YAML. LangGraph does
> the opposite — it makes **every step explicit**: nodes, edges, and a typed state
> object you control completely. This is the framework you reach for when you need
> control, transparency, and testability.

---

## The one mental model

LangGraph models an agent as a **directed graph (state machine)**. A shared, typed **state** object flows through **nodes** (plain Python functions that read and write state), routed by **edges** (including *conditional* edges that branch on state contents):

```
        ┌─────────────────────────────┐
        │   shared typed State         │
        │   {messages, result, ...}    │
        └─────────────────────────────┘
   START → [worker] ──conditional──▶ [evaluator] ──┐
              ▲                                     │
              └──────── "retry" ◀───────────────────┤
                                  "good enough" → END
```

The killer insight from Lab 1: **nodes are just Python functions** — they don't have to call an LLM at all. LangGraph is a general workflow engine that happens to be great for agents. State in, state out, routed by edges you define.

---

## Key concepts, precisely

**`StateGraph` + typed state** — you define a `TypedDict` (or Pydantic) describing every field that flows through the graph. This typed state is the *single source of truth*; nodes mutate it. (Contrast: in the Week 1 loop, state was an implicit `messages` list — here it's explicit and typed.)

**Nodes** — functions `(state) -> state_update`. Can be LLM calls, tool executions, or arbitrary logic.

**Edges** — wiring. `START`/`END` are special. **Conditional edges** are the whole point: a router function reads state (e.g., "did the LLM emit `tool_calls`?") and returns the name of the next node. *This is the agent loop, made explicit as a graph cycle.*

**`ToolNode`** — built-in node that executes any tool calls in the LLM's output and writes results back to state. Saves you the dispatch boilerplate.

**Checkpointing (persistent memory)** — `MemorySaver` (in-memory, dev) or `SqliteSaver` (survives restarts). Combined with a `thread_id`, you get **per-user persistent conversations** for free. This is the cleanest memory model in the whole course — understand it well.

**The evaluator pattern (Lab 4, the Sidekick)** — a *worker* node attempts the task; an *evaluator* node (separate LLM, structured `EvaluatorOutput`) judges the result; a conditional edge **loops back to retry or terminates**. This is self-correction as a graph — and it's the conceptual seed for Corrective RAG (Week 7) and the code-agent fix loop (Week 8).

---

## What an interviewer is really testing

- *"Why model an agent as a graph instead of using a higher-level SDK?"* → Explicit, inspectable state; arbitrary control flow (cycles, branches, retries); easy to unit-test each node; persistence via checkpointing. You trade boilerplate for control. Reach for it when behaviour must be precise and debuggable.
- *"How does LangGraph handle the agent loop?"* → As a **cycle in the graph**: an LLM node → conditional edge → `ToolNode` → back to the LLM node, until the router sends it to `END`. The Week 1 `while not done` loop, drawn as a graph.
- *"How do you give an agent memory across sessions?"* → Checkpointing (`SqliteSaver`) keyed by `thread_id`. Each thread is an isolated, persistent conversation.

---

## Tradeoffs & gotchas

- **Verbosity vs control.** LangGraph makes you spell out state and edges. For a simple linear pipeline that's overkill — CrewAI/OpenAI SDK are faster to write. Pick LangGraph when the control flow is genuinely complex (loops, branches, human-in-the-loop interrupts).
- **State design is the hard part.** Get the typed state wrong and every node fights it. Design state first, nodes second.
- **Infinite loops are real.** A worker↔evaluator cycle with no retry cap will loop forever (and burn money). Always bound retries.
- **`thread_id` is the isolation key.** Forget it and all users share one conversation. It's the multi-tenancy primitive.
- **Jupyter + async** needs `nest_asyncio` (Lab 3) — a notebook-only quirk, not a LangGraph concept.

---

## Self-test

<details><summary>1. What flows through a LangGraph graph, and what mutates it?</summary>
A shared, typed state object (TypedDict/Pydantic). Nodes (Python functions) read it and return updates; edges route between nodes.</details>

<details><summary>2. How is the agent loop represented in LangGraph?</summary>
As a cycle: LLM node → conditional edge checking for tool_calls → ToolNode runs them → back to the LLM node, until the router routes to END.</details>

<details><summary>3. How do you get persistent per-user memory?</summary>
Checkpointing (SqliteSaver) plus a thread_id per user — each thread is an isolated, durable conversation restored on the next call.</details>

<details><summary>4. What is the evaluator pattern and why does it matter beyond this week?</summary>
A worker node produces output; a separate evaluator node scores it; a conditional edge retries or finishes. It's self-correction as a graph — the seed of Corrective RAG (W7) and the code-agent fix loop (W8).</details>

---

**Labs:** `1` StateGraph basics → `2` tools + conditional edges + checkpointing → `3` async + browser automation → `4` Sidekick (worker/evaluator/retry). App: `sidekick.py`.

**Next:** [Week 5 Primer](../5_autogen/PRIMER.md) — multi-agent as message passing, scaling to distributed runtimes.
