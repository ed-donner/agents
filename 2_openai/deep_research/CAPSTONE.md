# Capstone: Deep Research — How This Uses 2_openai Ideas

This folder is the **capstone research project** for the 2_openai course. It implements a production-style **Deep Research** agent that pulls together concepts from the labs and adds advanced features.

---

## 1. Ideas from 2_openai Labs

| Lab / Topic | Idea | Where in this project |
|-------------|------|------------------------|
| **1_lab1** | Agents, Runner, tracing | All agents use `Agent()`, `Runner.run()` / `Runner.run_streamed()`; `trace()`, `gen_trace_id()` in `research_manager.py` for observability. |
| **2_lab2** | Tools (`function_tool`), handoffs | `email_agent`: `send_email` as `@function_tool`; `email_agent` is a **handoff** from the manager. SendGrid setup and usage as in lab. |
| **2_lab2** | Agents as tools, agent collaboration | Planner, search, writer, evaluator, optimizer are **agents exposed as tools** via `.as_tool()`; the manager agent calls them. |
| **3_lab3** | Structured outputs (Pydantic) | Every agent uses `output_type=...` with Pydantic models: `ClarificationData`, `WebSearchPlan`, `ReportData`, `EvaluationFeedback`, `OptimizedReport`. |
| **3_lab3** | Guardrails | **Input guardrails** in `guardrails.py`: intent check (OpenAI API), PII detection (regex), length limits. Run before clarifying questions and before research. |
| **4_lab4** | Deep Research (plan → search → write) | Core pipeline: planner → search (WebSearchTool) → writer → email, extended with clarifier, evaluator, optimizer, and agentic manager. |
| **4_lab4** | WebSearchTool | `search_agent` uses `WebSearchTool(search_context_size="low")`; summaries feed the writer with a **Source:** line for citations. |

---

## 2. Capstone-Specific Features

| Feature | Description | Files |
|---------|-------------|--------|
| **Clarifying questions (OpenAI-style)** | First step: generate 3 questions; user can answer to focus the research. | `clarifier_agent.py`, `research_manager.refine_query_with_answers()`, `deep_research.py` UI |
| **Agentic manager** | Single manager agent with **tools** (planner, search, writer, evaluate, optimize) and **handoff** (email). Autonomously decides search rounds (cap: 2 rounds, up to 5 extra searches). | `manager_agent.py` |
| **Evaluator–optimizer loop** | Report is evaluated; if `needs_refinement`, optimizer produces an improved version before finalizing. | `evaluator_agent.py`, manager instructions |
| **Citation layer** | Search summaries end with `Source: <url or title>`; writer uses `[1]`, `[2]` in the body and adds `## Sources and References` at the end. | `search_agent.py`, `writer_agent.py` |
| **Input guardrails** | **Intent**: OpenAI call to accept/reject as research request. **PII**: regex for email, phone, postcode. **Length**: max query and total input. | `guardrails.py`, `research_manager.run()`, `deep_research.py` |
| **Recipient email** | Optional “Recipient email” in UI; passed into refined query so the email agent sends to that address (via tool arg `to_email`). | `email_agent.py`, `research_manager.refine_query_with_answers()`, `deep_research.py` |
| **Streaming** | Status and report streamed to the UI via `Runner.run_streamed(manager_agent, ...)` and `stream_events()`. | `research_manager.run()` |
| **Gradio two-phase UI** | Phase 1: Get clarifying questions → show Q1–Q3 and answer boxes. Phase 2: Run deep research → stream report. Optional recipient email field. | `deep_research.py` |
| **Share & Hugging Face** | `share=True` for gradio.live link; `app.py` entry point and README instructions for deploying as a Space. | `deep_research.py`, `app.py`, `README.md` |

---

## 3. Architecture (flow)

```
User query
    → Input guardrails (intent, PII, length)
    → Clarifying questions (3) → optional user answers
    → Refined query (+ optional recipient email)
    → Manager agent (autonomous):
          → search_planner (tool)
          → web_search (tool) × N  [optional 2nd round × up to 5]
          → write_report (tool)
          → evaluate_report (tool)
          → [if needs_refinement] optimize_report (tool)
          → handoff to Email agent (report + optional recipient)
    → Stream status + final report to UI (and email if requested)
```

---

## 4. File Map

| File | Role |
|------|------|
| `guardrails.py` | Input guardrails (OpenAI SDK for intent; regex for PII; length). |
| `clarifier_agent.py` | Generates 3 clarifying questions (structured output). |
| `planner_agent.py` | Plans 20 web searches (structured output); exposed as tool. |
| `search_agent.py` | One web search + summary + `Source:` line; exposed as tool. |
| `writer_agent.py` | Long report with [1], [2] and ## Sources; exposed as tool. |
| `evaluator_agent.py` | Score + suggestions + needs_refinement; evaluator + optimizer as tools. |
| `manager_agent.py` | Single agent with all tools + email handoff. |
| `email_agent.py` | Send report as HTML email (function_tool + handoff). |
| `research_manager.py` | Orchestrates guardrails, clarifier, refined query, streaming run. |
| `deep_research.py` | Gradio UI (two-phase, recipient email, guardrails on “Get questions”). |
| `app.py` | Entry point for Hugging Face Spaces. |
| `requirements.txt` | Dependencies (gradio, openai, openai-agents, etc.). |
| `README.md` | Run locally, deploy to HF, quick share. |
| `CAPSTONE.md` | This file: mapping from 2_openai ideas to the project. |

---

## 5. Running the Capstone

- **Local**: `pip install -r requirements.txt` then `python deep_research.py` (or `python app.py`). Set `OPENAI_API_KEY` and optionally SendGrid/env vars (see README).
- **Share link**: Running `deep_research.py` gives a gradio.live link (`share=True`).
- **Hugging Face**: Copy this folder into a Gradio Space, set `app_file: app.py` and secrets (e.g. `OPENAI_API_KEY`); see README.

This project is intended to be the single, comprehensive **Deep Research** capstone for 2_openai, using all the ideas above.
