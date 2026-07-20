# Enhanced AI Sidekick

An extended version of the week 4 sidekick, built on LangGraph. Adds GitHub tools and persistent cross-session memory on top of the base set.

## Extra tools

| Tool | What it does |
|---|---|
| `github_search_repos` | Search GitHub by keyword — find libraries and examples |
| `github_read_file` | Read any file from a public repo (`owner/repo:path/to/file`) |
| `github_list_issues` | List open issues on a repo, optionally filtered by label |
| `save_memory` | Persist a fact to SQLite — survives across sessions |
| `recall_memory` | Retrieve a stored fact by key |
| `list_memories` | Show everything the sidekick has remembered |

Everything from the base sidekick is also included: Playwright, web search, Wikipedia, Python REPL, file management, push notifications.

## Setup

```bash
pip install langgraph langchain langchain-openai langchain-community \
            langchain-experimental playwright PyGithub gradio python-dotenv
playwright install chromium
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here       # optional — unlocks GitHub tools
PUSHOVER_TOKEN=your_token_here     # optional
PUSHOVER_USER=your_user_key_here   # optional
```

## Run

```bash
python app.py
```

## Architecture

```
app.py              — Gradio UI
sidekick.py         — LangGraph graph: worker → tools → evaluator loop
sidekick_tools.py   — All tool definitions
sandbox/            — File I/O sandbox (gitignored)
sidekick_memory.db  — Persistent memory store (gitignored)
knowledge_base/     — Optional personal context files (gitignored)
```
