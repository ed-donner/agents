# Nicholas Dean — Complete Agentic AI Engineering

My work through Ed Donner's agentic course, one folder per week (module). Each `weekN/` has a
**minimal** deliverable + a short `SUMMARY.md`. Companion to my digital twin
(github.com/N-D20/digital-twin), whose memory I grow with each course.

| Week | Module | Built |
|------|--------|-------|
| 1 | Foundations (no framework) | `career_conversation.py` — tool-using career-chat agent |
| 2 | OpenAI Agents SDK | `deep_research.py` — plan → parallel search → write |
| 3 | CrewAI | `research_crew.py` — sequential Researcher → Writer crew |
| 4 | LangGraph | `graph_agent.py` — worker+ToolNode graph with memory |
| 5 | AutoGen | `reflection_team.py` — Writer/Critic round-robin until APPROVE |
| 6 | MCP | `accounts_server.py` + `trader.py` — write & consume an MCP server |

## Run

Env is managed by `uv` at the repo root (`pyproject.toml` / `uv.lock`).

```bash
uv run python community_contributions/NicholasDean/week1/career_conversation.py
```

Keys in a gitignored `.env`: `OPENAI_API_KEY` (required); `PUSHOVER_USER` / `PUSHOVER_TOKEN`
(optional — for the phone-push tools).
