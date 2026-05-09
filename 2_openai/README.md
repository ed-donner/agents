# Week 2 — OpenAI Agents SDK

**Goal:** Use OpenAI's lightweight, production-ready Agents SDK to build single and multi-agent systems with minimal boilerplate.

---

## Labs

### Lab 1 — Introduction to the Agents SDK (`1_lab1.ipynb`)
- Creating an `Agent` with just three fields: `name`, `instructions`, and `model`
- Running agents with `Runner.run()` and inspecting the result
- Using the **Trace** viewer for debugging agent execution step by step
- Understanding the minimal viable agent structure before adding complexity

### Lab 2 — Multi-Agent Workflows & Handoffs (`2_lab2.ipynb`)
- Converting agents into reusable tools with `as_tool()`
- Creating function tools with the `@function_tool` decorator
- Implementing **agent handoffs** — one agent passing control to another
- Building a cold-sales email pipeline: three agents with different tones (professional, engaging, concise) + a selector agent that picks the best output
- Integrating **SendGrid** for real email delivery from within the agent system

### Lab 3 — Multi-Model Support & Guardrails (`3_lab3.ipynb`)
- Plugging in alternative LLM providers via OpenAI-compatible endpoints: DeepSeek, Gemini, Groq, Llama
- Using **Pydantic `BaseModel`** for structured, typed LLM outputs
- Adding **input guardrails** with the `@input_guardrail` decorator
- Implementing tripwire conditions that intercept and block invalid user requests before agent execution

### Lab 4 — Deep Research Pipeline (`4_lab4.ipynb`)
- Building a full multi-agent research system:
  - **Planner agent** — designs a set of targeted search queries
  - **Search agents** — each uses OpenAI's `WebSearchTool` to retrieve results
  - **Writer agent** — synthesises findings into a structured report (`ReportData` output schema)
  - **Email agent** — delivers the final report
- Using `async/await` throughout for non-blocking execution
- Coordinating multiple specialised agents in a sequential pipeline

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| `Agent` | Core object: name, instructions, model |
| `Runner.run()` | Executes an agent and returns a result |
| Trace inspection | Step-by-step debugging of agent execution |
| `as_tool()` | Wrap an agent so another agent can call it as a tool |
| `@function_tool` | Decorator to expose a Python function as an agent tool |
| Handoffs | Transfer of control from one agent to another |
| Structured outputs | Pydantic models for typed, validated responses |
| Input guardrails | `@input_guardrail` + tripwire to validate requests before execution |
| `WebSearchTool` | Built-in tool for live web search |
| Async patterns | `async/await` for concurrent multi-agent execution |

---

## Files

```
2_openai/
├── 1_lab1.ipynb    # Agents SDK basics
├── 2_lab2.ipynb    # Multi-agent workflows + handoffs + SendGrid
├── 3_lab3.ipynb    # Multi-model support + guardrails
└── 4_lab4.ipynb    # Deep research pipeline (async + WebSearch)
```
