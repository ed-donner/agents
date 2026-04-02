# Career Sprint Sidekick (Week 4 community contribution)

A **bounded career task** assistant: research a company and role, align with a local profile, and produce talking points plus a short outreach draft - validated by a **worker -> tools -> evaluator** loop and **SQLite checkpointing**. Built for *Master AI Agents in 30 days* (LangGraph week).

## What this project demonstrates


| Week 4 theme                    | Here                                                                                                           |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Days 1-2 - Graph + state**    | `CareerSprintState` (`TypedDict`) with `add_messages` reducer; explicit nodes and edges.                       |
| **Day 3 - Persistence**         | `AsyncSqliteSaver` -> `checkpoints/career_sprint.db` (WAL mode).                                               |
| **Day 3 - Conditional routing** | Worker routes to `ToolNode` or evaluator; evaluator routes to `END` or back to worker.                         |
| **Day 4 - Structured outputs**  | `SprintRubricAssessment` (Pydantic) for the evaluator; Gradio UI.                                              |
| **Day 5 - Tools**               | Web search (Serper or DuckDuckGo fallback), `read_career_profile`, Wikipedia, Python REPL, sandbox file tools. |


**Not included:** Playwright browser automation (optional in the course). Search + file + profile read cover the "tooling" learning goals without a browser install.

## Layout

- `graph.py` - LangGraph definition, default sprint rubric, `CareerSprintGraph.run_turn`.
- `tools.py` - Tool wiring; sandbox root is `sandbox/`; optional profile is `me/summary.txt`.
- `app.py` - Gradio app: **one `thread_id` per UI session** (reset starts a new thread and new compiled app instance).
- `checkpoints/` - Created at runtime (gitignored) for SQLite checkpoints.

## Setup

```bash
cd 4_langgraph/community_contributions/sammyloto_career_sprint
python3 -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt
cp .env.example .env
# Set OPENAI_API_KEY; optionally SERPER_API_KEY for stronger search
```

## Run

```bash
python app.py
```

Open the URL shown (default `http://127.0.0.1:7860`). Fill **company** and **role**, adjust **success criteria** if you like, then send a sprint request.

## Optional: personal profile (continuity with Week 1 style RAG)

Add a short bio under `me/summary.txt` (skills, goals, voice). The `read_career_profile` tool lets the worker tailor pitches without bundling Chroma in this submission.

## Optional: LangSmith

To trace runs in LangSmith, set in `.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=sammyloto-career-sprint
```

## Attribution

Patterns are **inspired by** the course Sidekick lab (`4_lab4` / `sidekick.py`)