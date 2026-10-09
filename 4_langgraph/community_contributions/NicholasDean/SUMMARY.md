# Week 4 - LangGraph

Lower-level than CrewAI: you draw the agent as an explicit **graph** of nodes and edges, and
LangGraph manages the state flowing through it. Great when you need loops, branching and memory.

- **Five concepts:** **Graph** (`StateGraph(State)`), **State** (a `TypedDict`), **Node** (a function
  `State -> partial State`), **Edge** (transition), and the **reducer** (how state updates merge).
- **State + reducer:** annotate a field with a reducer so updates *combine* instead of overwrite -
  `messages: Annotated[list, add_messages]` appends new messages automatically. One pass through the
  graph = a **super-step**; reducers apply within it.
- **Wiring:** `add_node("name", fn)`, `add_edge(a, b)`, and **`add_conditional_edges(src, router, {key: dest})`**
  where the router inspects state and returns a key. `START` / `END` are the entry/exit.
- **Tools:** `llm.bind_tools(tools)` lets the LLM emit tool calls; the prebuilt **`ToolNode(tools)`**
  executes them. Route worker -> tools -> worker until no tool calls remain (a ReAct loop).
- **Memory / persistence:** `graph.compile(checkpointer=MemorySaver())` (or `SqliteSaver`) snapshots
  state between super-steps; pass `config={"configurable": {"thread_id": ...}}` to keep a conversation.
- **Structured output:** `llm.with_structured_output(Model)` - used by Sidekick's evaluator to return
  `success_criteria_met` / `feedback` reliably.
- The module capstone, **Sidekick**, adds an evaluator node: worker does the work, an evaluator checks
  it against a `success_criteria`, and routes back to the worker until it passes (tools include
  Playwright browser, files, Python REPL, web search, push).

**Built:** `sidekick.py` - the full Sidekick: a worker LLM (with `calculator` + `save_note` tools)
works against a `success_criteria`, then an **evaluator** node grades the result with structured
output (`EvaluatorOutput`) and either ends (criteria met / needs the user) or routes back to the
worker with feedback to try again. `add_messages` state, `ToolNode`, two conditional edges, and a
`MemorySaver` checkpointer. The evaluator loop is what makes it a Sidekick, not just a tool agent.

## Distilled learning

**ELI5:** LangGraph is a flowchart for an LLM. You define a shared clipboard (**State**), some boxes
(**nodes** - usually "ask the LLM" and "run the tools"), and arrows (**edges**) - including
*if/else* arrows that look at the clipboard to decide where to go next. A **reducer** says how each
box's edits get added to the clipboard (e.g. "append to the message list"). A **checkpointer** saves
the clipboard, so giving the same `thread_id` next time continues the conversation.

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]            # reducer: append, don't overwrite

graph.add_conditional_edges("worker", route, {"tools": "tools", END: END})  # loop or stop
graph.add_edge("tools", "worker")
app = graph.compile(checkpointer=MemorySaver())        # memory per thread_id
```
