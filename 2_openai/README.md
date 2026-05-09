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

---

## Setup

```bash
pip install -r requirements.txt
```

Pinned versions (tested May 2026):

```
openai>=1.78.0
openai-agents>=0.0.19
pydantic>=2.11.4
python-dotenv>=1.1.0
sendgrid>=6.11.0
gradio>=5.29.1
```

Requires `OPENAI_API_KEY` in `.env`. Lab 2 and 4 require `SENDGRID_API_KEY` for email delivery.  
Lab 3 optionally uses `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `GROQ_API_KEY` for multi-model agents.

> **Cost guide:** Labs 1–3 use `gpt-4o-mini` (~$0.002–0.10/run). Lab 4 uses `WebSearchTool` (~$0.025/search call) — a full deep research run costs ~$0.10–0.50. Cost banners are shown at the top of each notebook.
