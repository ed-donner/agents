# Week 2 Primer — The OpenAI Agents SDK

> Read before the labs. Week 1 made you build the agent loop by hand. This week
> hands you a production SDK that hides the loop — your job is to understand
> *what it's hiding* so you can debug it when it misbehaves.

---

## The one mental model

The OpenAI Agents SDK takes the `while not done` loop you wrote in Week 1 and makes it a one-liner: `Runner.run(agent)`. An **Agent** is now just a named bundle of `instructions + model + tools`. You stopped writing the loop; you started *composing agents*.

The new superpower is **composition** — three ways agents combine:

```
  Agent-as-tool          Handoff                 Pipeline
  ┌─────────┐            ┌─────────┐             ┌──────┐  ┌──────┐  ┌──────┐
  │ manager │            │ triage  │             │planner│→│search│→│writer│
  └────┬────┘            └────┬────┘             └──────┘  └──────┘  └──────┘
   calls │ as tools       hands │ control off       output feeds next
   ┌─────┴─────┐          ┌─────┴─────┐
   ▼     ▼     ▼          ▼           ▼
 spanish english ...    billing     tech
 (manager keeps         (control LEAVES
  control)               the triage agent)
```

The crucial distinction: **`as_tool()` keeps control** (the caller gets the result back and continues), while a **handoff transfers control** (the new agent takes over and the original is done). Mixing these up is the #1 conceptual error this week.

---

## Key concepts, precisely

**`Agent(name, instructions, model)`** — the minimal unit. `Runner.run(agent, input)` executes the loop and returns a result you can inspect.

**`@function_tool`** — decorator that turns a plain Python function into a tool, auto-generating the JSON schema from your type hints and docstring. (Week 1 you wrote that schema by hand; now it's inferred.)

**`agent.as_tool()`** — wrap a whole agent so another agent can call it like a function. This is how you build a manager that delegates to specialists *and gets their answers back*.

**Handoffs** — list other agents in `handoffs=[...]`. The LLM can choose to *transfer the conversation* to one of them. Control leaves the current agent. Used for routing (triage → the right specialist).

**Guardrails** (`@input_guardrail`) — a check that runs *before* the agent and can trip a tripwire to block the request. This is your first taste of safety-as-code (deepened in Week 7 Lab 5).

**Structured outputs** — set an `output_type` (Pydantic) so the agent returns a typed object, not free text. Essential for pipelines where one agent's output is the next's input.

**Tracing** — the SDK records every step (LLM calls, tool calls, handoffs). The trace viewer is your debugger. *Learn to read it* — in an interview, "how do you debug a misbehaving agent?" → "I read the trace to see exactly which tool it called with what args and where it went wrong."

---

## What an interviewer is really testing

- *"When would you use a handoff vs an agent-as-tool?"* → Handoff when the conversation should **move** to a specialist and not come back (routing/triage). Agent-as-tool when the caller needs the **result returned** to keep working (delegation). This single question separates people who've read the docs from people who've built with the SDK.
- *"Why use the SDK instead of raw API calls?"* → Less boilerplate, built-in tracing, structured handoffs/guardrails, and battle-tested loop handling. But you should know it's *still the Week 1 loop underneath* — the SDK is convenience, not magic.

---

## Tradeoffs & gotchas

- **Framework lock-in vs control.** The SDK is opinionated. When you need full control over routing logic and state, LangGraph (Week 4) is the explicit-state alternative. Know both and when to reach for each.
- **Handoffs are one-way by default.** Control doesn't automatically return. If you need a round-trip, use `as_tool()`.
- **Guardrails fail-open if you let them.** If your guardrail check errors and you don't handle it, the request may pass through unchecked. Fail *closed* on safety checks (a recurring Week 7 theme).
- **The deep research pipeline (Lab 4) is async.** Parallel search agents run with `asyncio`. Understand why: web searches are I/O-bound, so running them concurrently is a big latency win.

---

## Self-test

<details><summary>1. Handoff vs as_tool — control flow difference?</summary>
Handoff transfers control to the new agent (doesn't return). as_tool calls the agent as a function and returns its result to the caller, which keeps control.</details>

<details><summary>2. What does @function_tool save you from writing?</summary>
The hand-written JSON schema. It infers name/params/types from your signature, type hints, and docstring.</details>

<details><summary>3. Where does the Week 1 agent loop go in the SDK?</summary>
Inside Runner.run(). The SDK runs the call-tool-loop-until-done cycle for you; you compose agents instead of writing the loop.</details>

<details><summary>4. Why is the deep-research pipeline async?</summary>
Searches are I/O-bound; running them concurrently with asyncio cuts total latency dramatically vs running them one at a time.</details>

---

**Labs:** `1` SDK basics + traces → `2` handoffs + as_tool + SendGrid → `3` multi-model + guardrails → `4` async deep-research pipeline.

**Next:** [Week 3 Primer](../3_crew/PRIMER.md) — a *declarative* take on multi-agent teams.
