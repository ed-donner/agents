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

open the `main.ipynb` notebook and run the cells.


