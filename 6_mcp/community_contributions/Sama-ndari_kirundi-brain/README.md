# Kirundi Study Brain (Week 6 MCP)

Local-first **Kirundi (Rundi)** study coach exposed as a **FastMCP** server. An OpenAI Agents SDK demo attaches over stdio, calls path-jailed Brain tools, and tutors from a Markdown corpus — not from thin air.

Inspired by the course trading/MCP labs and pro patterns like `asket-mcp` (Brain + profile + gated writes), scoped to Burundi language learning.

## Architecture

```
demo_agent.py  →  MCPServerStdio  →  server.py (FastMCP)
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
              brain/*.md           SQLite profile        ask / grade
              (path jail)          (data/)               (OpenAI + retrieve)
```

## Tools

| Tool | Purpose |
|------|---------|
| `brain_list_files` | List corpus entries |
| `brain_read_file` | Read a lesson |
| `brain_search_notes` | Keyword search in `.md` |
| `brain_write_markdown` | Add/update lesson (`overwrite` gated) |
| `brain_delete_file` | Delete lesson (confirm gated) |
| `profile_get` / `profile_update` | Learner level, goals, mistakes |
| `ask_kirundi_tutor` | Retrieve + grounded answer |
| `grade_kirundi_answer` | Score a short reply |
| `kirundi_brain_info` | Paths / version / config |

## Setup

```bash
cd 6_mcp/community_contributions/Sama-ndari_kirundi-brain
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
```

### Run MCP server alone (stdio — Cursor / Claude Desktop)

```bash
python server.py
```

Example Cursor `mcp.json` fragment (adjust absolute paths):

```json
{
  "mcpServers": {
    "kirundi-study-brain": {
      "command": "python",
      "args": ["/ABS/PATH/Sama-ndari_kirundi-brain/server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "KIRUNDI_BRAIN_DIR": "/ABS/PATH/Sama-ndari_kirundi-brain/brain",
        "KIRUNDI_BRAIN_DATA_DIR": "/ABS/PATH/Sama-ndari_kirundi-brain/data"
      }
    }
  }
}
```

### Run agent demo

```bash
python demo_agent.py "How do I say thank you in Kirundi?"
python demo_agent.py "Quiz me on greetings"
```

## Sample corpus

Bundled under `brain/`: greetings, courtesy, numbers, food. Point `KIRUNDI_BRAIN_DIR` at a larger phrase bank when you have one.

## Env

| Variable | Role |
|----------|------|
| `OPENAI_API_KEY` | Required for agent demo + `ask` / `grade` |
| `KIRUNDI_BRAIN_MODEL` | Default `gpt-4o-mini` |
| `KIRUNDI_BRAIN_DIR` | Corpus root (default: `./brain`) |
| `KIRUNDI_BRAIN_DATA_DIR` | SQLite dir (default: `./data`) |

Do not commit `.env` or `data/*.sqlite3`.

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
