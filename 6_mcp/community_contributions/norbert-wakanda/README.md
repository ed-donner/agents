**Terminal Issue Tracker -- AI-Powered Developer Debugging Assistant**

**What it does:** This tool automatically monitors your terminal activity log for errors, logs them to a local SQLite database with the commands that resolved them, and lets you search past issues via a Gradio UI -- all powered by an LLM agent using MCP (Model Context Protocol).

**Project structure:**

| File | Purpose |
|---|---|
| `startlog` | Bash script that starts a terminal logging session, writing all activity to `terminal_activity.log` |
| `issues.py` | `IssueStore` class -- SQLite CRUD for issues + log file read/clear |
| `issues_server.py` | MCP server exposing 4 tools: `add_issue`, `search_issues`, `read_log_file`, `clear_log` |
| `mcp_agent.py` | Two AI agents: one to monitor logs and record errors, one to search known issues |
| `main.ipynb` | Notebook with periodic log monitoring + Gradio search UI |
| `create_db.py` / `empty_db.py` | Database setup and reset utilities |

**How to use:**

1. **Start logging** -- run `source startlog` in your terminal to begin capturing activity to `terminal_activity.log`
2. **Open `main.ipynb`** -- the notebook runs two things:
   - A periodic background task that checks the log for errors every N minutes, logs issues via MCP, then clears the log
   - A Gradio web interface where you type an issue description and get back matching past issues with their fix commands
3. **Work normally** -- use your terminal as usual; errors get automatically detected and stored
4. **Search later** -- when you hit a familiar error, search the Gradio UI to find the command you used last time