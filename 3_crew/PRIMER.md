# Week 3 Primer — CrewAI: Declarative Role-Based Teams

> Read before the projects. Week 2 composed agents in *code*. CrewAI composes
> them in *YAML* — a "team of role-players" abstraction. The mental shift is from
> "I write the orchestration" to "I declare the roles and let the framework run."

---

## The one mental model

CrewAI models a multi-agent system as a **company org chart**. You declare **agents** (each with a `role`, `goal`, and `backstory` — literally a persona) and **tasks** (units of work with a description and expected output), then assemble them into a **crew** that runs either:

```
  SEQUENTIAL process              HIERARCHICAL process
  ┌──────────┐                          ┌─────────┐
  │ researcher│                         │ manager │  (auto-delegates)
  └────┬─────┘                          └────┬────┘
       │ output feeds                   ┌────┼────┐
       ▼                                ▼    ▼    ▼
  ┌──────────┐                       spec1 spec2 spec3
  │ analyst  │                       (manager decides who does what)
  └──────────┘
```

The big idea: **identity (agent) is separated from work (task).** An agent's persona is reusable; tasks wire them together. You configure all of it in `agents.yaml` / `tasks.yaml` — almost no orchestration Python.

---

## Key concepts, precisely

**Agent = role + goal + backstory.** These three fields are persona prompt-engineering. The backstory measurably shifts behaviour ("You are a skeptical financial analyst with 20 years..."). This is declarative system-prompting.

**Task = description + expected_output (+ optional tools, output Pydantic model).** Tasks are the verbs; agents are the nouns.

**Sequential process** — tasks run in order; each output becomes the next task's context. Predictable, debuggable, the default.

**Hierarchical process** — a manager agent you don't write the logic for *autonomously decides* which specialist handles each subtask. More autonomous, less predictable — use when the decomposition genuinely varies per input.

**Tools** — built-ins like `SerperDevTool` (web search), or custom tools by subclassing `BaseTool`. The agent uses them without you managing the tool-call loop (CrewAI runs it).

**Memory (the stock_picker project)** — three tiers:
- *Long-term* (SQLite) — persists across runs
- *Short-term* (RAG/vector) — within-run semantic recall
- *Entity* — tracks named people/companies across tasks

This is your first real "stateful agent" — memory that survives process restarts.

---

## What an interviewer is really testing

- *"Sequential vs hierarchical — when each?"* → Sequential when the pipeline is fixed and you want determinism/debuggability. Hierarchical when the task decomposition varies and you're willing to trade predictability for autonomy. Senior tell: mention that hierarchical is harder to test and debug, so you default to sequential until you *need* dynamic delegation.
- *"How is CrewAI different from the OpenAI SDK?"* → Declarative (YAML config) and role-centric vs imperative (Python) and loop-centric. CrewAI optimises for "describe a team," the SDK for "compose functions." Same underlying agent loop.
- *"Why does a backstory matter?"* → It's persona conditioning that steers the model's tone, priorities, and reasoning style — declarative prompt engineering.

---

## Tradeoffs & gotchas

- **Declarative = less control.** When the YAML abstraction fights you (custom routing, mid-run branching), you fall back to LangGraph's explicit state machine (Week 4). Know the escape hatch.
- **Hierarchical is non-deterministic.** The manager's delegation can differ run-to-run. Hard to write regression tests against. Don't reach for it by default.
- **Memory has real storage costs and staleness.** Long-term SQLite memory can accumulate junk; entity memory can track stale facts. Memory is a feature *and* a liability.
- **Windows pain.** CrewAI needs MS Build Tools; `PYTHONUTF8=1` fixes unicode errors on `crewai create`. (Noted in the README — interviewers won't ask, but it'll bite you.)

---

## Self-test

<details><summary>1. What three fields define a CrewAI agent and what are they really?</summary>
role, goal, backstory — declarative persona prompt-engineering that conditions the model's behaviour.</details>

<details><summary>2. Sequential vs hierarchical process?</summary>
Sequential: tasks run in fixed order, each output feeds the next — deterministic. Hierarchical: a manager agent auto-delegates subtasks to specialists — autonomous but non-deterministic.</details>

<details><summary>3. Name the three memory tiers in stock_picker and their lifespans.</summary>
Long-term (SQLite, across runs), short-term (RAG/vector, within a run), entity (named-entity tracking across tasks).</details>

<details><summary>4. When would you abandon CrewAI for LangGraph?</summary>
When you need explicit control over state and routing that the declarative YAML abstraction can't express cleanly (mid-run branching, custom loops, fine-grained state).</details>

---

**Projects:** `debate/` (sequential, 3 roles) → `financial_researcher/` (tools + pipeline) → `stock_picker/` (hierarchical + 3-tier memory + custom tool).

**Next:** [Week 4 Primer](../4_langgraph/PRIMER.md) — drop the abstraction, model agents as explicit state machines.
