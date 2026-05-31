# MCP Server Project

## Purpose
Exposes a custom database to the LLM allowing it to craft dynamic SQL statements to answer user's queries

## Run
1. `uv run python app.py`


## Testing the MCP Server with MCP Inspector
1. cd `mcp_server` directory
2. run
    npx @modelcontextprotocol/inspector uv --directory . run server.py
> NOTE: NodeJS must be set up


## Terminal Recording with Asciinema
    asciinema record --command "uv run app.py" mcp.cast

### Recording
https://asciinema.org/a/bQ7cKKEIvoqvDflVrMXx21Z6d
