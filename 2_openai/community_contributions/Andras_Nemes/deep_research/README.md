# Deep Research extensions

Three extensions to the course `deep_research` project, built on top of each other.

## Challenge 1: Clarifying questions

`clarifier_agent.py` returns exactly three clarifying questions for the query, using a structured
output. The Gradio UI (`deep_research.py`) runs in two stages: the first button shows the questions
with answer boxes, the second runs the research with the query and the answers.

## Challenge 2: Clarification propagation and an evaluator

The answers flow into every stage. `build_*_input` helpers in `research_manager.py` add them to the
planner, search, writer and evaluator inputs, and each agent's instructions tell it to respect them.
`evaluator_agent.py` returns `{aligned, feedback}` after the searches. If the results fall short, the
manager re-plans with the feedback and searches again, up to `MAX_REFINEMENTS` extra rounds, before
writing the report.

## Challenge 3: Autonomous manager agent

`research_agent.py` replaces the fixed Python orchestration with one manager agent that holds the
specialists as tools (agents-as-tools, no handoffs) plus an email tool that never raises. The
instructions suggest a flow, but the model decides how many searches to run and when to loop.
`deep_research_agentic.py` is the UI for this version; it logs every tool call to the console via
`RunHooks`. Clarification stays as a UI step because a single run cannot pause for user input.
LLM orchestration can skip steps, so the hooks record which tools were called and if the manager
never called the email tool, the code sends the report by email after the run.

## Files

| File | Purpose |
|---|---|
| `deep_research.py` | UI for challenges 1 and 2 (fixed orchestration) |
| `deep_research_agentic.py` | UI for challenge 3 (autonomous manager) |
| `research_manager.py` | Fixed orchestration with evaluator loop |
| `research_agent.py` | Autonomous manager agent |
| `clarifier_agent.py`, `planner_agent.py`, `search_agent.py`, `evaluator_agent.py`, `writer_agent.py`, `email_agent.py` | The specialist agents |
| `messenger.py` | SMTP email with Pushover push fallback |
| `test_offline.py` | Offline tests, no API calls |

## Setup

Add to the repo-root `.env`:

- `OPENAI_API_KEY` (required)
- `EMAIL_ADDRESS`, `EMAIL_SMTP_SERVER`, `EMAIL_APP_PASSWORD` for email, as in lab 2
- `PUSHOVER_USER` and `PUSHOVER_TOKEN` if you set `USE_EMAIL=false` to use push instead
- `DEFAULT_MODEL_NAME` to override the model (default `gpt-5.4-mini`)

If no email or push is configured, the email step logs a failure and the run continues.

Note: `WebSearchTool` is a paid hosted tool, about 1 cent per call.

## Running

From this folder:

```bash
uv run deep_research.py          # challenges 1 and 2
uv run deep_research_agentic.py  # challenge 3
uv run test_offline.py           # offline tests
```
