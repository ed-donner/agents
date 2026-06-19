# Date MCP Server + Client

A minimal Model Context Protocol (MCP) server that exposes a single tool `current_date` and `current_time` returning today's date in ISO format, and a matching client that lists tools and invokes it.

## Files
- `date_server.py`: MCP server exposing `current_date`
- `date_client.py`: Client helpers using stdio to connect via `uv`
- `main.ipynb`: Walkthrough notebook to try it end-to-end

## Prereqs
- `uv` available on your PATH
- Setup Conda like this
conda create -n mcpdev python=3.11 -y
conda activate mcpdev

# MUST install MCP first
pip install mcp

# Install correct OpenAI Agent SDK
pip install openai-agents

# Utilities you asked for
pip install python-dotenv ipython jupyterlab
pip install rich typer black isort


## Execution

The repository includes a minimal MCP server (`date_server.py`) that also exposes an
`ask_llm` tool powered by OpenAI, and a simple stdio-based client (`date_client.py`).

1) Configure an OpenAI API key (optional but required for `ask_llm`):

Create a `.env` file in this folder or export the env var. Example `.env`:

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # optional; defaults to gpt-4o-mini

If `OPENAI_API_KEY` is not set the server will still run, but `ask_llm` will return
an informative message indicating the LLM is not configured.

2) Install requirements and start the notebook or run the server/client manually.

Open the `main.ipynb` notebook and run the cells for an end-to-end walkthrough, or
run the server and client manually:

Run the MCP server (stdio transport expected by the client):

python date_server.py

In another terminal, you can run the client (`date_client.py` is an async helper —
the notebook demonstrates usage). The client will list tools and can call
`current_date`, `current_time`, and `ask_llm` (if configured).

Notes:
- The server uses `OPENAI_MODEL` (env) to control which model to call.
- Error handling has been added for the LLM call so runtime errors are returned as
	readable messages to calling clients.



