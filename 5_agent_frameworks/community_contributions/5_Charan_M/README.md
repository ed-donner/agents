# Python Agent Framework (smolagents)

This folder contains a from-scratch implementation of an AI agent using Python and the `smolagents` framework. It breaks down the process of building a fully capable, tool-calling agent into distinct, easy-to-understand stages.

The agent uses a shared SQLite todo board to plan tasks and track its own progress.

## Setup

First, install the required packages:

```bash
pip install -r requirements.txt
```

Ensure you have your API keys in your `.env` file at the root of the workspace (e.g., `GEMINI_API_KEY`).

## The Scripts

The files are broken down sequentially to demonstrate how an agent is built up layer by layer:

1. **`create_agent.py`**
   - *What it does:* The foundational file. It initializes the LLM model and gives the agent its system prompt (its personality and core instructions).
   - *Run it:* `python create_agent.py`

2. **`message.py`**
   - *What it does:* Tests the agent by sending it a simple prompt (asking for a Spanish greeting) and receiving a reply, without any tools attached yet.
   - *Run it:* `python message.py`

3. **`add_tools.py`**
   - *What it does:* Introduces the agent to the outside world. It hooks up the typed functions from `tools.py` so the agent can read and modify the SQLite todo board.
   - *Run it:* `python add_tools.py`

4. **`add_mcp.py`**
   - *What it does:* Simulates connecting external MCP tool servers (like a filesystem). The agent is given tools to read and write files in the local `workspace/` directory.
   - *Run it:* `python add_mcp.py`

5. **`loop_goal.py`**
   - *What it does:* The grand finale. The agent is placed into a continuous loop, given a goal ("Write a short haiku about Madrid into madrid.txt"), and has access to all tools (the board and the filesystem). The agent will plan its own steps, execute them, and complete the goal on its own.
   - *Run it:* `python loop_goal.py`

## Auxiliary Files

*   **`tools.py`**: The definitions for the `@tool` decorated functions the agent uses to interact with the board (`show_todos`, `plan_steps`, `complete_task`).
*   **`board.py`**: A simple wrapper around `sqlite3` to persist the agent's task list locally.
