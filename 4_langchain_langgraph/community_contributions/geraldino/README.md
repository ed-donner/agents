# 🤖 Sidekick — Personal AI Co-Worker Extended

An agentic AI assistant built with LangGraph, LangChain, and Gradio. Sidekick takes your requests, plans them into subtasks, asks clarifying questions when needed, executes using real tools, and evaluates its own work all with persistent memory across sessions.

---

## Features

### 1. Clarifying Questions (max 3)

Before starting any task, a dedicated **Clarifier agent** checks if the request is clear enough. If not, it asks up to 3 targeted questions one at a time to gather the context needed. Once satisfied (or after 3 questions), it hands off to the planner. This prevents the worker from wasting cycles on ambiguous instructions.

### 2. Planning Agent

A **Planner agent** sits between the clarifier and the worker. It breaks the user's request into an ordered list of 2–6 concrete subtasks. This keeps the worker focused and makes complex tasks manageable.

### 3. Worker Agent with Tools

The **Worker agent** executes the plan using a rich set of tools:

- 🌐 **Playwright browser** — navigate and scrape websites
- 🔍 **Google Serper search** — real-time web search
- 🐍 **Python REPL** — run code and calculations
- 📁 **File management** — read/write files in a sandbox
- 📖 **Wikipedia** — look up reference information
- 📲 **Push notifications** — send alerts via Pushover

### 4. Evaluator Agent

After every worker response, an **Evaluator agent** checks whether the success criteria has been met. If not, it provides structured feedback and sends the worker back to try again. It also detects when the worker is stuck and flags that user input is needed.

### 5. SQL Persistent Memory

Conversation state is saved to a local SQLite database (`sidekick_memory.db`) using LangGraph's `AsyncSqliteSaver`. Every message, plan, and feedback is persisted. Restart the app and pick up exactly where you left off.

### 6. User Login & Chat History

A simple login system (`users.db`) stores usernames, hashed passwords, and each user's unique `sidekick_id`. Returning users get their full conversation history restored automatically. New usernames are auto-registered on first login.

### 7. Smart Context Window

To keep LLM calls efficient and avoid token limits, only the **last 10 messages** are fed into the worker on each turn. The trimming logic ensures tool call pairs are never orphaned, preventing OpenAI 400 errors.

---

## Architecture

```
START
  │
  ▼
Clarifier ──► (needs clarification?) ──► END (wait for user)
  │
  ▼ (clear enough)
Planner
  │
  ▼
Worker ──► (tool calls?) ──► Tools ──┐
  │                                  │
  │◄─────────────────────────────────┘
  │
  ▼
Evaluator
  │
  ├──► (success or user input needed?) ──► END
  │
  └──► (not done?) ──► Worker (loop)
```

---

## Project Structure

```
├── app.py              # Gradio UI — login, chat, session management
├── sidekick.py         # Core agent — state, nodes, graph, memory
├── sidekick_tools.py   # Tool definitions — browser, search, files, etc.
├── sidekick_memory.db  # Auto-created — LangGraph graph state (SQLite)
├── users.db            # Auto-created — user accounts (SQLite)
├── sandbox/            # Auto-created — file management working directory
└── .env                # API keys (not committed)
```

---

## Setup

### 1. Install dependencies

```bash
pip install gradio langgraph langchain langchain-openai langchain-community
pip install langchain-experimental playwright aiosqlite
pip install langgraph-checkpoint-sqlite
pip install langchain-community[playwright]
playwright install chromium
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
PUSHOVER_TOKEN=your_pushover_token      # optional
PUSHOVER_USER=your_pushover_user_key    # optional
```

### 3. Create the sandbox directory (optional)

```bash
mkdir sandbox
```

### 4. Run the app

```bash
python app.py
# or with uv:
uv run app.py
```

Then open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser.

---

## Usage

1. **Login** — enter any username and password. First time = auto-registered. Returning users get history restored.
2. **Type your request** — e.g. *"Find the top 3 cheapest flights from Abuja to London on June 2nd, 2026. Send a push notificaition on the cheapest flight to me"*
3. **Set success criteria (optional)** — e.g. *"Give me prices, airlines, and booking links"*
4. **Click Go!** — the agent clarifies, plans, executes, and evaluates automatically
5. **Reply to questions** — if the clarifier or worker asks something, just respond and click Go! again
6. **Clear Chat** — clears the display but keeps your SQL memory intact
7. **Logout** — returns to login screen and frees browser resources

---

## How Login Works

- Usernames are **case-insensitive** and **trimmed of whitespace**
- Passwords are hashed with **SHA-256** before storage
- Each user has a unique `sidekick_id` that maps to their LangGraph thread
- New username + any password = **auto-registration**
- Existing username + correct password = **login + history restored**
- Existing username + wrong password = **rejected**

---

## Built With

- [LangGraph](https://github.com/langchain-ai/langgraph) — multi-agent graph orchestration
- [LangChain](https://github.com/langchain-ai/langchain) — LLM tooling and integrations
- [OpenAI GPT-4o-mini](https://openai.com) — worker, planner, clarifier, evaluator LLMs
- [Gradio](https://gradio.app) — web UI
- [Playwright](https://playwright.dev) — browser automation
- [SQLite + aiosqlite](https://docs.python.org/3/library/sqlite3.html) — persistent memory and user auth

---

## Author

Built as a Week 5 assessment project, extending the Sidekick architecture from the LangChain Agents course.