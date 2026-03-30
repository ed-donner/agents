# env_align_mcp

Small **read-only** MCP server that helps agents (and humans) keep `.env` aligned with `.env.example` without dumping real secrets into traces.

## Problem

Teams drift between documented variables and local `.env` files. Models often guess names or miss new keys. This server exposes **structured, local-only** tools so an agent can report gaps factually.

## Tools

| Tool | Purpose |
|------|---------|
| `compare_env_to_example` | Keys in example but missing in `.env`, keys in `.env` not in example, duplicates, empty placeholders in the example |
| `parse_env_example` | Row-level view of `.env.example` (non-empty defaults, inline `#` hints) |
| `mask_env_preview` | Lists keys with **masked** values for safe logging |

All paths are resolved under `project_root`; path traversal outside that root is rejected.

## Setup

```bash
cd 6_mcp/community_contributions/env_align_mcp
uv sync
```

Set `OPENAI_API_KEY` in your environment (or `.env` in this folder) to run the demo agent.

## Run the server (stdio)

```bash
uv run server.py
```

## Demo: OpenAI Agents SDK + MCP

```bash
uv run demo_agent.py
```

Optional: `ENV_ALIGN_MODEL=gpt-4.1-mini` (default) or another model your key supports.

## Fixture

`fixtures/sample_project` ships `.env.example` plus `sample.env` (tracked stand-in for `.env`, since `.env` is gitignored in this repo). Pass `env_filename="sample.env"` when calling the tools against the fixture.

## Learning goals

- FastMCP `@mcp.tool()` with typed parameters and JSON-friendly return strings
- Safe filesystem scope for agent-callable tools
- Masking values before they appear in agent or platform traces

## License

MIT (match course / your preference when contributing upstream).
