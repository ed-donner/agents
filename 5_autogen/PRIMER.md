# Week 5 Primer — AutoGen: Message-Driven & Distributed Agents

> Read before the labs. Weeks 2–4 ran agents in one process. AutoGen introduces
> the idea that agents are **independent actors that communicate by passing
> messages** — and that this model scales from one process to many machines.

---

## The one mental model

AutoGen has **two layers**, and the whole week is about understanding why both exist:

```
  AgentChat (high-level)              Core (low-level)
  "Model → Message → Agent"          actor model + message bus
  ┌────────────┐                     ┌──────────────────────────┐
  │AssistantAgent│ quick to build    │  runtime (the bus)        │
  └────────────┘                     │  ┌────┐ msg  ┌────┐       │
  RoundRobinGroupChat = a team       │  │ A  │─────▶│ B  │       │
                                     │  └────┘      └────┘       │
                                     │  @message_handler routes  │
                                     └──────────────────────────┘
                                     SingleThreaded → one process
                                     GrpcWorker     → many machines
```

The mental model is the **actor model**: each agent is an independent unit that reacts to messages addressed to it. In AgentChat you barely see this; in Core you build it directly; with the gRPC runtime those actors live in *different processes or machines* and talk over the network. Same abstraction, three scales.

---

## Key concepts, precisely

**AgentChat (Lab 1–2)** — the fast path. `Model → Message → Agent`: make a `ModelClient`, send `TextMessage`s to an `AssistantAgent` that has function tools. `RoundRobinGroupChat` groups agents into a **team** that take turns until a termination condition fires. `MultiModalMessage` carries images; `output_content_type` enforces Pydantic structured output. `LangChainToolAdapter` lets you reuse LangChain tools — cross-framework interop is a real theme.

**Core (Lab 3)** — the actor runtime. `SingleThreadedAgentRuntime` is the message bus. You subclass `RoutedAgent` and decorate methods with `@message_handler` to react to specific message *types*. Agents register with the runtime and communicate **only** through asynchronous messages — no direct function calls. This decoupling is what makes distribution possible.

**Distributed (Lab 4)** — swap the runtime for `GrpcWorkerAgentRuntimeHost` and the *same agents* now run across processes/machines, communicating over gRPC. A host delegates to remote workers and collects results. This is the payoff: the actor abstraction means scaling out is a runtime swap, not a rewrite.

---

## What an interviewer is really testing

- *"When would you use a message-driven / actor architecture for agents?"* → When agents must run concurrently, be independently deployable/scalable, or live across machines; when you want loose coupling so one agent's failure doesn't block others. The trade is added complexity vs the in-process simplicity of the OpenAI SDK or LangGraph.
- *"AgentChat vs Core — why two APIs?"* → AgentChat is rapid, high-level (prototype fast). Core is the low-level runtime for distributed, message-driven systems (production scale-out). You start in AgentChat and drop to Core only when you need distribution or custom message routing.
- *"How do AutoGen agents communicate?"* → Asynchronous message passing through a runtime/bus, not direct calls — the decoupling that enables the gRPC distributed runtime.

---

## Tradeoffs & gotchas

- **Distribution is complexity you must justify.** gRPC runtimes add ops burden (service discovery, serialization, partial failure). Most agent systems run fine in one process — reach for distributed only when you have a real scale or isolation reason.
- **Message-driven ≠ easier.** Async message passing is harder to trace than a linear call stack. Good logging/tracing is mandatory (Week 7 Lab 4).
- **Two APIs = a learning tax.** Don't conflate AgentChat objects with Core objects; they're different layers.
- **Termination conditions matter.** A `RoundRobinGroupChat` without a solid termination condition can loop indefinitely — same bounded-loop discipline as LangGraph.

---

## Self-test

<details><summary>1. What architectural model underlies AutoGen Core?</summary>
The actor model: independent agents that react to messages addressed to them, communicating asynchronously through a runtime/bus rather than direct calls.</details>

<details><summary>2. AgentChat vs Core — pick one and why.</summary>
AgentChat for rapid high-level prototyping; Core for low-level, message-driven, distributable systems. Start high, drop to Core when you need distribution or custom routing.</details>

<details><summary>3. What changes between Lab 3 (single-threaded) and Lab 4 (distributed)?</summary>
Only the runtime: SingleThreadedAgentRuntime → GrpcWorkerAgentRuntimeHost. The same agents now run across processes/machines over gRPC. The actor abstraction makes scale-out a runtime swap.</details>

<details><summary>4. What does @message_handler do?</summary>
Binds an agent method to a specific incoming message type, so the runtime routes matching messages to that handler — the core of message-driven routing.</details>

---

**Labs:** `1` AgentChat + SQLite booking → `2` multimodal + teams + MCP → `3` Core runtime + message handlers → `4` distributed gRPC.

**Next:** [Week 6 Primer](../6_mcp/PRIMER.md) — standardising how *any* agent connects to *any* tool.
