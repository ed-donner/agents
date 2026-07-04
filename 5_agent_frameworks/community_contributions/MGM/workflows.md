# agentics Workflows
The Pydantic AI and the Strands agents can do workflows, but they take pretty different shapes. Here's how each maps to what your `agent_framework` graph does (writer → translator → human approval gate → conditional save → formatted output, with MCP filesystem access).

## Pydantic AI (`pydantic_graph`)
Pydantic AI's `pydantic_graph` module is a typed graph library, conceptually close to what you already have — nodes are classes/functions with typed inputs/outputs, edges are inferred from return-type annotations (or built explicitly in the newer beta `GraphBuilder` API).

- **Agents as nodes**: each `BaseNode` can wrap a `pydantic_ai.Agent` call.
- **Conditional branching**: the beta API has explicit `g.decision()` / `g.match()` constructs for exactly your save/skip fork; the classic API does it by returning different node types from a node's `run()` method (e.g. return either a `SaveNode` or `FormatNode` instance) and the graph follows whichever type came back.
- **Human-in-the-loop**: supported via durable execution — a node can raise/return something that pauses the graph, waits for a real HTTP request or external event with the user's decision, and resumes from the same node. This is more "production async approval" than your script's blocking terminal `input()`, but you can also just call `input()` inside a node the same way if you don't need durability.
- **MCP tools**: Pydantic AI agents support MCP servers natively as tool sources, so your filesystem-MCP piece maps over directly.
- **State**: the graph carries a typed `State` dataclass passed to every node — closer to a straightforward dict/dataclass than the pending/commit buffer semantics in `agent_framework`.

It's a very natural fit — arguably a smaller, more Pythonic version of the same idea.

## Strands Agents (AWS)
Strands' `GraphBuilder` (in `strands.multiagent`) is also a good fit, with a slightly different flavor:

```python
from strands import Agent
from strands.multiagent import GraphBuilder

builder = GraphBuilder()
builder.add_node(writer_agent, "writer")
builder.add_node(translator_agent, "translator")
builder.add_node(router_fn, "router")          # plain function node
builder.add_node(saver_fn, "saver")
builder.add_node(formatter_fn, "formatter")

builder.add_edge("writer", "translator")
builder.add_edge("translator", "router")
builder.add_edge("router", "saver", condition=should_save)
builder.add_edge("saver", "formatter")
builder.add_edge("router", "formatter", condition=should_skip)

graph = builder.build()
result = graph("A high-performance organic energy drink for programmers.")
```

- **Conditional edges**: first-class — `add_edge(..., condition=fn)`, same shape as your `should_save`/`should_skip`.
- **Cycles**: Strands graphs explicitly support cyclic topologies too (review/revise loops), which `agent_framework` also supports but Strands documents it as a headline feature.
- **Custom/non-agent nodes**: you can add plain functions as nodes (not just `Agent` instances) — useful for your router/saver/formatter logic, same as your `Executor` subclasses.
- **Human-in-the-loop**: Strands has a dedicated "Human in the Loop" concept plus an **Interrupts** primitive and a built-in `handoff_to_user` tool that pauses execution, preserves context, and resumes when a human responds — more structured than a bare `input()` call, and it plugs into session persistence so a pause can survive a process restart.
- **MCP tools**: Strands has native MCP tool support (`Model Context Protocol (MCP) Tools` in their docs), same idea as your `FilesystemMCP`.
- **State**: state flows through `invocation_state` passed at graph invocation, and node output is automatically passed to dependent nodes — you wouldn't need the manual `ctx.set_state`/`ctx.get_state` dance, output propagation is built into edge semantics.

## Rough fit summary
| | `agent_framework` (yours) | Pydantic AI (`pydantic_graph`) | Strands (`GraphBuilder`) |
|---|---|---|---|
| Typed nodes/edges | yes | yes (very strict, Pydantic-validated) | looser, string node IDs |
| Conditional edges | yes | yes (decision/match, or type-based) | yes (`condition=` callable) |
| Cycles/loops | supported | supported | supported, well-documented |
| Human-in-loop | manual (`input()`) | durable-execution pause/resume | built-in interrupts + `handoff_to_user` |
| MCP tools | yes | yes | yes |
| Ecosystem bias | Microsoft/.NET-parity | framework-agnostic, FastAPI-style | AWS/Bedrock-centric, deploys well to Lambda/AgentCore |
