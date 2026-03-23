# Deep Research Agent

An enhanced deep research system built with the OpenAI Agents SDK, extending the
course's original `deep_research` project.

## What is different

| Feature | Original | This version |
|---|---|---|
| Manager | Python class with sequential `Runner.run()` calls | True `Agent` with sub-agents as tools and a handoff |
| Clarification | None | Auto-generated scoping questions before any search |
| Query refinement | Fixed plan | Sufficiency agent triggers extra search rounds |
| Evaluation loop | None | Evaluator agent scores the report; writer revises if score < 7 |
| Guardrails | None | Input safety classifier and output quality gate |
| Streaming | Status strings only | `Runner.run_streamed` on the orchestrator |
| Model settings | Not set | `ModelSettings(temperature, max_tokens, top_p)` on every agent |

## Architecture

```
User query
   |
   v
ClarifierAgent --> 3 clarifying questions (scope shown in status)
   |
   v
ResearchOrchestrator (Agent with tools + handoff)
   |-- plan_searches          --> PlannerAgent
   |-- run_parallel_searches  --> N x SearchAgent (asyncio.gather)
   |-- check_sufficiency      --> SufficiencyAgent  -| loop up to 2x
   |-- write_report           --> WriterAgent        |
   |-- evaluate_report        --> EvaluatorAgent  ---| loop up to 1x
   +-- handoff                --> EmailAgent
```

## Guardrails

- Input: LLM-based safety classifier blocks harmful or illegal queries.
- Output: Heuristic gate ensures the report is at least 200 words and contains
  no placeholder text. A full LLM-based check is stubbed and documented for
  production use.

## Setup

```bash
uv pip install openai-agents sendgrid python-dotenv gradio ddgs
```

Required environment variables (add to `.env`):

```
OPENROUTER_API_KEY=...
SENDGRID_API_KEY=...
SENDGRID_FROM_EMAIL=your-verified-sender@example.com
SENDGRID_TO_EMAIL=your-recipient@example.com
```

To switch provider, set `RESEARCH_PROVIDER` to `openrouter`, `openai`, or `groq`.
Note: Groq does not support structured outputs (json_schema) so use openrouter or openai.

## Run

```bash
python app.py
```

Enter a research topic and click **Run Research**. The agent clarifies scope,
runs parallel searches, evaluates the results, and writes a detailed report.
