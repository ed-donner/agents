"""
Week 6 Lab 3 — Exercise: explore MCP marketplaces and integrate servers (3 approaches)

The lab groups MCP usage into three patterns:

1. **Local / self-contained** — A process on your machine; data stays local (e.g. SQLite memory).
2. **Local process, remote APIs** — Still stdio on your machine, but tools call the network
   (e.g. `mcp-server-fetch` loads URLs).
3. **Remote transport** — Your client connects over HTTP (Streamable HTTP) to a server hosted
   elsewhere. URLs usually come from a marketplace or your own deployment.

Where to browse servers (marketplaces & catalogs)
------------------------------------------------
- Official reference servers: https://github.com/modelcontextprotocol/servers
- Smithery (discover + hosted installs): https://smithery.ai
- Glama MCP directory: https://glama.ai/mcp/servers
- Anthropic remote MCP notes: https://docs.anthropic.com/en/docs/agents-and-tools/remote-mcp-servers

Requirements
------------
- `OPENAI_API_KEY` in `.env` (repo root) or environment.
- **Demo 1**: Node.js + `npx` (for `mcp-memory-libsql`).
- **Demo 2**: `uvx` available (for `mcp-server-fetch` from PyPI).
- **Demo 3** (optional): set `LAB3_REMOTE_MCP_URL` to a Streamable HTTP MCP endpoint from a
  marketplace or your own deploy (see Cloudflare guide in the lab notebook).

Run (from the `6_mcp` directory, same as the course notebooks)
----------------------------------------------------------------
    cd 6_mcp
    uv run python community_contributions/manish_tiwari/lab3_solution.py --demo 1
    uv run python community_contributions/manish_tiwari/lab3_solution.py --demo 2
    uv run python community_contributions/manish_tiwari/lab3_solution.py --demo 3
    uv run python community_contributions/manish_tiwari/lab3_solution.py --demo all
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp

# Paths: this file lives in .../6_mcp/community_contributions/manish_tiwari/
_SOLUTION_DIR = Path(__file__).resolve().parent
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MCP_CWD = _SOLUTION_DIR.parents[1]  # .../6_mcp

load_dotenv(_REPO_ROOT / ".env", override=True)

DEFAULT_MODEL = os.environ.get("LAB3_OPENAI_MODEL", "gpt-4.1-mini")


def _require_openai_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your environment or in agents/.env")


async def demo_1_local_memory_graph() -> None:
    """Approach 1: marketplace server, fully local data (LibSQL file under this folder)."""
    _SOLUTION_DIR.joinpath("memory").mkdir(parents=True, exist_ok=True)

    params = {
        "command": "npx",
        "args": ["-y", "mcp-memory-libsql"],
        "env": {"LIBSQL_URL": "file:./memory/lab3_graph.db"},
        "cwd": str(_SOLUTION_DIR),
    }

    instructions = (
        "You have a persistent knowledge graph. Use create_entities / create_relations / "
        "search_nodes to store and recall facts about the user."
    )
    store = (
        "My name is Ed. I am learning MCP. Please save me as an entity with a short observation."
    )
    recall = "What do you remember about Ed? Use search_nodes or read_graph if helpful."

    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as mcp:
        agent = Agent(
            name="lab3_local_memory",
            instructions=instructions,
            model=DEFAULT_MODEL,
            mcp_servers=[mcp],
        )
        with trace("lab3_type1_store"):
            r1 = await Runner.run(agent, store)
        print("--- Type 1 (store) ---\n", r1.final_output, "\n")

        with trace("lab3_type1_recall"):
            r2 = await Runner.run(agent, recall)
        print("--- Type 1 (recall) ---\n", r2.final_output, "\n")


async def demo_2_local_fetch_web() -> None:
    """Approach 2: local MCP process that calls the public web (no extra API key)."""
    params = {
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "cwd": str(_MCP_CWD),
        "env": {**os.environ},
    }

    instructions = (
        "You can fetch public web pages with your tools. Summarize briefly and cite the page."
    )
    request = (
        "Use your fetch tool on https://example.com and say what the page is about in one sentence."
    )

    async with MCPServerStdio(params=params, client_session_timeout_seconds=90) as mcp:
        agent = Agent(
            name="lab3_fetch",
            instructions=instructions,
            model=DEFAULT_MODEL,
            mcp_servers=[mcp],
        )
        with trace("lab3_type2_fetch"):
            result = await Runner.run(agent, request)
        print("--- Type 2 (local + web) ---\n", result.final_output, "\n")


async def demo_3_remote_streamable_http() -> None:
    """Approach 3: connect to a remotely hosted MCP server (Streamable HTTP)."""
    url = (os.environ.get("LAB3_REMOTE_MCP_URL") or "").strip()
    if not url:
        print(
            "--- Type 3 (remote) — skipped ---\n"
            "Set LAB3_REMOTE_MCP_URL to your server’s Streamable HTTP URL "
            "(from Smithery, Glama, Cloudflare, or your own deploy).\n"
            "Docs for this transport: "
            "https://modelcontextprotocol.io/specification/2025-03-26/basic/transports\n"
        )
        return

    params = {
        "url": url,
        "timeout": 30.0,
        "sse_read_timeout": 180.0,
    }

    instructions = (
        "You have tools from a remote MCP server. Use them when needed and answer clearly."
    )
    request = os.environ.get(
        "LAB3_REMOTE_PROMPT",
        "List what tools you have (by name) and run the simplest one if it needs no arguments.",
    )

    async with MCPServerStreamableHttp(
        params=params,
        client_session_timeout_seconds=120,
    ) as mcp:
        tools = await mcp.list_tools()
        print(f"--- Type 3: connected; {len(tools)} tools ---")
        agent = Agent(
            name="lab3_remote",
            instructions=instructions,
            model=DEFAULT_MODEL,
            mcp_servers=[mcp],
        )
        with trace("lab3_type3_remote"):
            result = await Runner.run(agent, request)
        print(result.final_output, "\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 3 MCP marketplace / three approaches demo")
    parser.add_argument(
        "--demo",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Which demo to run (default: all)",
    )
    args = parser.parse_args()

    _require_openai_key()

    if args.demo in ("1", "all"):
        await demo_1_local_memory_graph()
    if args.demo in ("2", "all"):
        await demo_2_local_fetch_web()
    if args.demo in ("3", "all"):
        await demo_3_remote_streamable_http()


if __name__ == "__main__":
    asyncio.run(main())
