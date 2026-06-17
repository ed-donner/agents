# Week 3 — CrewAI

**Goal:** Use CrewAI's declarative, YAML-driven approach to compose role-based multi-agent crews that collaborate through structured tasks.

---

## Projects

### Debate (`debate/`)
- Defining agents and tasks entirely in **YAML config files** (no boilerplate Python for structure)
- **Sequential process execution** — tasks run in order, each agent's output feeds the next
- Three-agent pipeline: Proposer → Opposer → Judge
- Understanding how CrewAI separates agent *identity* (role, goal, backstory) from task *instructions*

### Financial Researcher (`financial_researcher/`)
- Integrating external tools into agents — `SerperDevTool` for live web search
- Sequential researcher → analyst pipeline where the analyst receives the researcher's findings as context
- Writing final outputs to markdown files on disk
- How CrewAI agents can use tools without explicit tool-call loop management

### Stock Picker (`stock_picker/`)
- **Hierarchical process** — a manager agent that autonomously delegates subtasks to specialist agents
- Pydantic structured outputs: `TrendingCompany` and `TrendingCompanyResearch` models for typed results
- Multi-tier **memory systems**:
  - Long-term memory (SQLite)
  - Short-term memory (RAG/vector)
  - Entity memory (named entity tracking)
- Custom `PushNotificationTool` — building your own CrewAI tool from scratch
- Stateful agent systems where memory persists across runs

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| YAML config | Agents and tasks defined declaratively in `agents.yaml` / `tasks.yaml` |
| Sequential process | Tasks execute in order; output of one becomes input of the next |
| Hierarchical process | Manager agent delegates to specialists automatically |
| `SerperDevTool` | Built-in web search tool for research agents |
| Structured outputs | Pydantic models (`BaseModel`) for typed crew results |
| Long-term memory | SQLite-backed persistence across crew runs |
| Short-term memory | RAG (vector) memory for within-run context |
| Entity memory | Tracks named entities (people, companies) across tasks |
| Custom tools | Subclass `BaseTool` to expose any Python function as a CrewAI tool |

---

## How to Run

> **Windows users:** Install Microsoft Build Tools first (see root `SETUP-PC.md` gotcha #4).

```bash
# Install the CrewAI CLI tool (pinned version)
uv tool install crewai==0.130.0 --python 3.12

# Run any crew project from its directory
cd debate
crewai run
```

If you see a unicode error on `crewai create crew`, run first:
```powershell
$env:PYTHONUTF8 = "1"
```

---

## Files

```
3_crew/
├── debate/
│   ├── src/debate/
│   │   ├── config/agents.yaml   # Agent definitions
│   │   ├── config/tasks.yaml    # Task definitions
│   │   └── crew.py              # Crew assembly
│   └── pyproject.toml
├── financial_researcher/
│   └── src/financial_researcher/
│       ├── config/agents.yaml
│       ├── config/tasks.yaml
│       └── crew.py
├── stock_picker/
│   └── src/stock_picker/
│       ├── config/agents.yaml
│       ├── config/tasks.yaml
│       ├── crew.py
│       └── tools/               # Custom tool definitions
└── README.md
```
