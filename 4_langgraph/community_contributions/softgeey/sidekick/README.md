# SideKick — PM AI Assistant

A personal agentic AI assistant built with **LangGraph**, **FastAPI**, and **OpenRouter**.  
Designed for a Senior Project Manager: email drafting, meeting prep, project tracking, and research.

---

## Architecture

```
User (Browser)
    │
    ▼
FastAPI  (/chat endpoint)
    │
    ▼
LangGraph Graph
    ├── router_node       → classifies intent
    ├── tool_fetcher_node → loads live data (Gmail / Calendar / Tavily)
    └── specialist nodes
        ├── email_agent
        ├── calendar_agent
        ├── tasks_agent
        ├── research_agent
        └── general_agent
```

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- An [OpenRouter](https://openrouter.ai) API key
- A [Tavily](https://tavily.com) API key (free tier available)
- A Google Cloud project with Gmail + Calendar API enabled *(optional)*

---

## Quick Start

### 1. Install dependencies
```bash
uv sync
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 3. Google OAuth setup (optional — for Gmail + Calendar)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project, enable **Gmail API** and **Google Calendar API**
3. Credentials → Create OAuth 2.0 Client ID → Desktop App
4. Download JSON → save as `credentials.json` in the project root
5. First run opens a browser for OAuth consent; token saved to `token.json`

> Without credentials.json, email and calendar features degrade gracefully.

### 4. Run
```bash
uv run python main.py
```

Open **http://127.0.0.1:8000** in your browser.

---

## Capabilities

| Intent    | What it does                                                   |
|-----------|----------------------------------------------------------------|
| Email     | Fetches recent inbox, summarises, drafts replies               |
| Calendar  | Shows upcoming events, generates meeting prep briefs           |
| Tasks     | Structures priorities, drafts CEO status reports, flags risks  |
| Research  | Web search via Tavily, synthesises competitive intel           |
| General   | Open-ended Q&A, writing help, strategic advice                 |

The router automatically classifies your message — no manual mode switching needed.

---

## Project Structure

```
sidekick/
├── main.py               # Entry point
├── app.py                # FastAPI app + /chat endpoint
├── config.py             # Environment config
├── llm_client.py         # OpenRouter LLM wrapper
├── google_auth.py        # Google OAuth2 helper
├── graph.py              # LangGraph graph definition
├── agents/
│   ├── state.py          # Shared AgentState schema
│   ├── router.py         # Intent classification node
│   ├── tool_fetcher.py   # Pre-fetches live data
│   ├── email_agent.py    # Email specialist
│   ├── calendar_agent.py # Calendar specialist
│   ├── tasks_agent.py    # Task/project specialist
│   ├── research_agent.py # Research specialist
│   └── general_agent.py  # General fallback
├── tools/
│   ├── gmail_tool.py     # Gmail API integration
│   ├── calendar_tool.py  # Google Calendar integration
│   └── research_tool.py  # Tavily web search
├── ui/
│   ├── static/style.css
│   ├── static/app.js
│   └── templates/index.html
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Switching Models

Edit OPENROUTER_MODEL in .env:

```
OPENROUTER_MODEL=anthropic/claude-opus-4-5
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_MODEL=google/gemini-2.0-flash-exp
```

---

## Security Notes

- All secrets live in .env — never commit it
- credentials.json and token.json are in .gitignore
- Conversation history is in-memory only, resets on server restart
- No data is logged or persisted to disk
