# Lab 2 exercise — MCP date server + client

My solution for the Week 6 MCP lab exercise in `6_mcp/2_lab2.ipynb`.

**What I built**

- `date_server.py` — FastMCP server with a `get_current_date` tool.
- `date_client.py` — stdio MCP client helpers (list tools, call tools, session context, mapping tools for OpenAI’s API).
- `2_lab2_date_exercise.ipynb` — walkthrough with notes before each code cell.

**What I wanted to learn**

How to define an MCP tool, connect it from the Agents SDK, then do the same flow with a lower-level client and finally with raw Chat Completions so the pieces don’t feel like magic.

**How I run it**

- Open the notebook from this folder, or start Jupyter with cwd at the repo root so path resolution in the first cell works.
- `OPENAI_API_KEY` in the repo `.env` (same as the rest of the course).


