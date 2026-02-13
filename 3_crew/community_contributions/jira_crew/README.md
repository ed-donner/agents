# Jira Support Crew

A **CrewAI multi-agent** app that helps users with **Jira**: list/create epics and sprints, list boards, and answer “how to” questions. Combines the [engineering_team](https://github.com/ed-donner/agents/tree/main/agents/3_crew/engineering_team) CrewAI pattern with [JIRA_MCP](https://github.com/padmanabh275/JIRA_MCP)-style Jira APIs.

## Features

- **Jira specialist agent** – Uses tools to list epics, sprints, boards and to create epics/sprints (Jira Cloud REST + Agile APIs).
- **Docs agent** – Answers conceptual Jira questions (e.g. “What is an epic?”) from documentation knowledge.
- **Synthesizer agent** – Turns specialist + docs outputs into one clear, user-friendly answer.
- **Streamlit UI** – Simple chat interface to ask questions and see answers.
- **LLM** – **Local Ollama** by default (no API key); optional **Gemini** when `USE_OLLAMA=false`.

## Setup

1. **Clone / use this folder** (e.g. under `agents/3_crew/community_contributions/jira_crew`).

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Local Ollama (default)**
   - Install [Ollama](https://ollama.com) and start it.
   - Pull a model: `ollama pull llama3.2` (or set `OLLAMA_MODEL` in `.env` to another model, e.g. `llama2`, `mistral`).
   - No API key needed; the app uses `http://localhost:11434` by default.

4. **Optional: use Gemini instead**
   - In `.env`: `USE_OLLAMA=false` and `GOOGLE_API_KEY=your-gemini-api-key`.

5. **Optional: live Jira**
   - In `.env`: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`.
   - Example base URL: `https://padmanabhbosamia.atlassian.net` (project **SCRUM**, board **1**).
   - Copy `env.example` to `.env` and fill in your Jira API token ([Create API token](https://id.atlassian.com/manage-profile/security/api-tokens)).

   Example `.env` (Ollama + Jira):
   ```env
   USE_OLLAMA=true
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   JIRA_BASE_URL=https://your-site.atlassian.net
   JIRA_EMAIL=you@example.com
   JIRA_API_TOKEN=your-jira-api-token
   ```

   Without Jira credentials, the app still runs: the docs agent answers conceptual questions, and the Jira specialist will report that Jira is not configured when tools are used.

## Run

**Streamlit (recommended):**
```bash
streamlit run app.py
```

**CLI (one-off question):**
```bash
# From the jira_crew folder, with src on PYTHONPATH
python -c "from jira_crew.main import run; print(run('List all epics'))"
# Or: python src/jira_crew/main.py "What is a sprint?"
```

## Project layout

- `app.py` – Streamlit chat frontend.
- `config.py` – Env/config for Ollama/Gemini and Jira.
- `src/jira_crew/` – CrewAI crew:
  - `crew.py` – Agents (jira_specialist, docs_agent, synthesizer) and tasks; Ollama (default) or Gemini LLM.
  - `config/agents.yaml`, `config/tasks.yaml` – Agent and task definitions.
  - `tools/jira_tools.py` – CrewAI tools: list_epics, list_boards, list_sprints, create_epic, create_sprint.
  - `main.py` – CLI entry point for the crew.

## References

- [CrewAI](https://www.crewai.com/)
- [Engineering Team crew](https://github.com/ed-donner/agents/tree/main/agents/3_crew/engineering_team) (same repo)
- [JIRA_MCP](https://github.com/padmanabh275/JIRA_MCP) – Jira MCP-style Epic/Sprint APIs
