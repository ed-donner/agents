# Week 6 — Model Context Protocol (MCP)

**Goal:** Understand and implement MCP — the open standard for connecting AI agents to external tools and resources in a portable, reusable way.

---

## Labs

### Lab 1 — Using Built-in MCP Servers (`1_lab1.ipynb`)
- What MCP is: a standardised protocol so any agent can talk to any tool server
- Spawning MCP servers with `MCPServerStdio` (stdio transport)
- Using pre-built servers: `mcp-server-fetch` (web), Playwright (browser), filesystem
- Calling `list_tools()` to discover what a server exposes at runtime
- Passing `mcp_servers` to OpenAI Agents to make all server tools available automatically
- Practical demos: browsing the web and writing files entirely through MCP tools

### Lab 2 — Building Custom MCP Servers (`2_lab2.ipynb`)
- Wrapping existing Python code (an accounts management system) into a **custom MCP server**
- Exposing Python functions as MCP tools using the MCP SDK
- Running your own server via `MCPServerStdio` alongside a client
- Creating an MCP client that converts server tools into OpenAI-compatible tool format
- Reading **MCP resources** (structured data exposed by a server, separate from tools)
- Full bidirectional integration: agent calls your server, server returns structured data

### Lab 3 — MCP Server Ecosystem (`3_lab3.ipynb`)
- MCP server taxonomy:
  - **Local-only** — memory graph database for persistent entity/relationship tracking
  - **Local-with-web-service** — Brave Search, Polygon.io market data (local process + remote API)
  - **Remote** — cloud-hosted MCP servers (limited availability)
- Configuring servers with environment variables for API keys and settings
- Handling rate limiting through smart caching strategies
- Integrating specialised domain services: financial markets (Polygon.io), web search (Brave), persistent memory (graph DB)

---

## Capstone App — Trading Floor Simulator

The most complex project in the course — a full multi-agent trading simulation powered entirely by MCP servers:

| Module | Role |
|--------|------|
| `accounts.py` / `accounts_server.py` | MCP server exposing trader account data and balance management |
| `market_server.py` | MCP server providing live market prices and order execution |
| `push_server.py` | MCP server for real-time push notifications to traders |
| `database.py` | SQLite backing store for accounts and trade history |
| Trader agents | Autonomous agents that connect to all three MCP servers to trade |

Key architectural insight: each agent only knows about MCP servers — the underlying implementation (SQLite, market simulation, push service) is completely hidden behind the protocol.

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| MCP protocol | Open standard for agent ↔ tool server communication |
| `MCPServerStdio` | Spawns an MCP server as a subprocess communicating over stdin/stdout |
| `list_tools()` | Discover available tools from any MCP server at runtime |
| `mcp_servers` parameter | Pass servers to OpenAI Agents to auto-expose all their tools |
| MCP resources | Structured data endpoints on a server (distinct from callable tools) |
| Custom MCP server | Python code wrapped with MCP SDK to become a server |
| Server taxonomy | Local-only / local-with-web-service / remote |
| Smart caching | Rate-limit mitigation by caching responses from external APIs |
| Multi-server orchestration | One agent connecting to multiple MCP servers simultaneously |

---

## MCP vs. Direct Tool Calls

| | Direct Tool Call | MCP Tool |
|--|-----------------|----------|
| Portability | Tied to one agent framework | Works with any MCP-compatible agent |
| Discovery | Hardcoded schema | Dynamic `list_tools()` at runtime |
| Implementation hiding | Partial | Full — server abstracts all details |
| Reuse | Manual per-framework wiring | Plug any agent into any server |

---

## Files

```
6_mcp/
├── 1_lab1.ipynb          # Using built-in MCP servers
├── 2_lab2.ipynb          # Building custom MCP servers
├── 3_lab3.ipynb          # MCP server ecosystem
├── accounts.py           # Account management logic
├── accounts_server.py    # MCP server wrapping accounts.py
├── market_server.py      # MCP server for market simulation
├── push_server.py        # MCP server for push notifications
└── database.py           # SQLite backing store
```

---

## Setup

```bash
pip install -r requirements.txt
```

Pinned versions (tested May 2026):

```
openai>=1.78.0
openai-agents>=0.0.19
python-dotenv>=1.1.0
requests>=2.32.3
```

**Node.js is also required** for JavaScript-based MCP servers (Playwright, filesystem, Brave Search).  
Install Node.js LTS from [nodejs.org](https://nodejs.org), then verify with `node --version`.

> **Windows users:** MCP subprocess spawning has a known issue on Windows. Use WSL2 as a workaround — see [setup/SETUP-WSL.md](../setup/SETUP-WSL.md).

Lab 3 requires `BRAVE_API_KEY` (free tier at [brave.com/search/api](https://brave.com/search/api)) and `POLYGON_API_KEY` (free tier at [polygon.io](https://polygon.io)).  
Lab 4 (Trading Floor) additionally requires `PUSHOVER_TOKEN`/`PUSHOVER_USER`.

> **Cost guide:** Labs 1–3 use `gpt-4.1-mini` (~$0.01–0.20/run). Lab 4 (Trading Floor) loops every 60 min by default — monitor your usage and stop when done (~$0.20–1.00/loop × 4 traders). Cost banners are at the top of each notebook.
