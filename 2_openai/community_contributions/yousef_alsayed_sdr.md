# SDR Multi-Agent Pipeline
### by Yousef Attaf ([@yousefattaff](https://github.com/yousefattaff))

> Full source code: **[github.com/yousefattaff/SDR_Multi_Agent](https://github.com/yousefattaff/SDR_Multi_Agent)**

An end-to-end **Sales Development Representative** pipeline built with the OpenAI Agents SDK — using only free-tier models from Groq and OpenRouter, with full **Langfuse** observability via OpenTelemetry.

Given a prospect company name, it researches the company, generates three personalised cold emails from different LLMs, picks the best one, and sends it via SendGrid.

Every concept from Labs 1–4 of Week 2 is used in one cohesive project.

---

## Pipeline

```
User input (prospect name)
        │
        ▼
[Input guardrail]        blocks personal names              (Lab 3)
        │
        ▼
[Research planner]       generates 3 search queries         (Lab 4)
   ┌────┼────┐
   ▼    ▼    ▼
[Search agents × 3]      parallel Tavily web search         (Lab 4)
   └────┼────┘
        ▼
[Research writer]        → structured ResearchSummary       (Lab 4)
        │
        ▼
[Sales manager]          orchestrates drafters              (Lab 2+3)
   ┌────┼────┐
   ▼    ▼    ▼
[Drafter 1]     [Drafter 2]      [Drafter 3]
professional    witty            concise                    (Lab 1+3)
   └────┼────┘
        │  picks best → handoff
        ▼
[Email Manager]          subject → HTML → SendGrid send     (Lab 2)
```

---

## What each lab contributes

| Lab | Concept | Where |
|-----|---------|-------|
| **Lab 1** | Multi-provider clients: Groq + OpenRouter via `OpenAIChatCompletionsModel` | `models.py` |
| **Lab 2** | `agent.as_tool()`, `handoffs`, `@function_tool`, SendGrid | `emailer.py`, `manager.py` |
| **Lab 3** | Pydantic `output_type`, `input_guardrail`, different model per agent | `schemas.py`, `drafters.py`, `manager.py` |
| **Lab 4** | Planner → parallel web search (Tavily) → synthesis writer | `research.py` |

---

## Model assignments (all free tier)

| Agent | Model | Provider |
|-------|-------|----------|
| Research planner | `llama-4-scout-17b` | Groq |
| Search agents (×3) | `llama-4-scout-17b` | Groq |
| Research writer | `qwen3-32b` | Groq |
| Professional drafter | `gpt-oss-120b` | Groq |
| Witty drafter | `gemma-4-31b-it:free` | OpenRouter |
| Concise drafter | `llama-4-scout-17b` | Groq |
| Sales manager | `owl-alpha` | OpenRouter |
| Name-check guardrail | `llama-4-scout-17b` | Groq |
| Subject writer | `gpt-oss-120b` | Groq |
| HTML converter | `llama-3.1-8b` | Groq |
| Email manager | `qwen3-32b` | Groq |

---

## Langfuse tracing

Uses `openinference-instrumentation-openai-agents` — the OpenTelemetry-based integration that automatically captures model names, token usage, span hierarchy, and generation types. Every agent call is grouped under a single `trace("SDR Pipeline")` in the Langfuse dashboard.

```python
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
OpenAIAgentsInstrumentor().instrument()
```

---

## Keys required

| Variable | Source |
|----------|--------|
| `OPENAI_API_KEY` | platform.openai.com |
| `GROQ_API_KEY` | console.groq.com (free) |
| `OPEN_ROUTER_API_KEY` | openrouter.ai (free) |
| `TAVILY_API_KEY` | tavily.com (free tier) |
| `SENDGRID_API_KEY` | sendgrid.com (free tier) |
| `SENDGRID_FROM_EMAIL` | your verified sender |
| `SENDGRID_TO_EMAIL` | recipient address |
| `LANGFUSE_PUBLIC_KEY` | cloud.langfuse.com (free) |
| `LANGFUSE_SECRET_KEY` | cloud.langfuse.com (free) |
