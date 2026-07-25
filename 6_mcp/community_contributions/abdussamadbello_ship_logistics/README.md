# Ship logistics MCP (demo)

Community contribution for **Week 6 — MCP**: a **synthetic** maritime logistics toolkit so agents can reason about **route / weather risk bands**, **security zones**, **static “crisis” alerts**, and **bunker-style fuel indices**, plus a **rough voyage cost stub**.

**Not for real navigation, chartering, insurance, sanctions compliance, or operational decisions.** All numbers and advisories are **static coursework data**.

## Ports (examples)

| Code   | Name        |
|--------|-------------|
| SGSIN  | Singapore   |
| NLRTM  | Rotterdam   |
| USLAX  | Los Angeles |
| AEJEA  | Jebel Ali   |
| CNYTN  | Yantian     |

## Tools

| Tool | Purpose |
|------|---------|
| `list_ports` | Valid port codes |
| `get_route_snapshot` | Distance, typical days, weather risk band, seasonal note |
| `get_security_advisory` | Piracy-style index for RED_SEA, GULF_GUINEA, MALACCA, HORN_AFRICA |
| `list_security_regions` | Region codes |
| `list_active_alerts` | Synthetic corridor / weather / compliance alerts |
| `get_fuel_price_index` | VLSFO-style $/mt + 7d trend % (snapshot) |
| `estimate_voyage_cost_stub` | Bunker + daily OPEX rough total |
| `corridor_summary` | Route + suggested security rows + fuel reference |

## Run the server (stdio)

From **this folder**:

```bash
python server.py
```

or:

```bash
python run.py
```

The MCP **wire protocol** runs over the process **stdin/stdout**. Anything that can **spawn** this command and attach pipes is a valid client.

---

## How to interact with this MCP

There are three common interfaces; pick one.

### 1. IDE / assistant (Cursor, Claude Code, etc.)

Register a **stdio** server that runs your interpreter and `server.py`, with **cwd** set to this folder so `import ship_logistics` resolves.

**Cursor** (example — adjust paths to your machine and venv):

```json
{
  "mcpServers": {
    "ship-logistics": {
      "command": "/absolute/path/to/agents/.venv/bin/python",
      "args": ["/absolute/path/to/agents/6_mcp/community_contributions/abdussamadbello_ship_logistics/server.py"],
      "cwd": "/absolute/path/to/agents/6_mcp/community_contributions/abdussamadbello_ship_logistics"
    }
  }
}
```

Put this under your user **MCP settings** (or project MCP config, depending on Cursor version). After reload, the model sees **tools** (`get_route_snapshot`, `corridor_summary`, …) like any other MCP server.

**Interaction model:** natural language → model chooses tools → MCP runs `server.py` subprocess → tool JSON/text back to the model. You do not call HTTP endpoints on this server unless you add a separate bridge (not included here).

### 2. OpenAI Agents SDK (course Week 6 pattern)

Use `MCPServerStdio` with a `command` + `args` that match the above (same idea as `1_lab1.ipynb`):

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

params = {
    "command": "/path/to/.venv/bin/python",
    "args": ["server.py"],
    "cwd": "/path/to/abdussamadbello_ship_logistics",
}

async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as mcp_server:
    agent = Agent(
        name="LogisticsAssistant",
        instructions="Use ship logistics tools for route, security, fuel, and cost stubs. Say when data is synthetic.",
        mcp_servers=[mcp_server],
    )
    result = await Runner.run(
        agent,
        "Summarize corridor SGSIN to NLRTM: weather risk, security, and rough fuel context.",
    )
    print(result.final_output)
```

Run that script with `cwd` or full paths so `server.py` starts in the contribution folder.

### 3. Low-level Python MCP client (no Agents SDK)

This repo includes **`client_demo.py`**: it spawns `server.py`, lists tools, and calls `corridor_summary` once.

```bash
cd 6_mcp/community_contributions/abdussamadbello_ship_logistics
python client_demo.py
```

Use the same `mcp.client.stdio` + `ClientSession` pattern if you need custom orchestration (see also `date_mcp_server_client/date_client.py` in community contributions).

## Dependencies

Uses `mcp` with `FastMCP` (same stack as the course `6_mcp` labs). Install from the course environment / `requirements.txt` at repo root.

## Why synthetic

Avoids API keys, moving market data, and **arbitrary outbound URLs** (SSRF review). Agents can still practice **multi-factor logistics reasoning** (weather + security + fuel + cost) on a fixed dataset.
