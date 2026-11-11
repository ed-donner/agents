# Week 6 - MCP (Model Context Protocol)

The capstone idea: stop hand-wiring tools into each agent. **MCP** is a client-server protocol that
exposes tools, resources and prompts behind a standard interface, so any MCP-aware agent can plug in.

- **Three pieces a server can expose:** **tools** (callable functions), **resources** (read-only
  content addressed by a URI), and **prompts** (templates).
- **Three transports:** **stdio** (spawn a local process), **SSE/HTTP** (streamable), and remote
  (hosted over HTTPS).
- **Write a server with FastMCP** - tiny:
  ```python
  from mcp.server.fastmcp import FastMCP
  mcp = FastMCP("accounts")

  @mcp.tool()
  def buy_shares(symbol: str, quantity: int) -> str: ...

  @mcp.resource("accounts://report")
  def report() -> str: ...

  mcp.run(transport="stdio")
  ```
- **Consume it from the OpenAI Agents SDK** - pass servers to the agent and tools are auto-discovered:
  ```python
  async with MCPServerStdio(params={"command": "uv", "args": ["run", "python", "server.py"]}) as s:
      agent = Agent(name="Trader", mcp_servers=[s], model="gpt-4o-mini")
      await Runner.run(agent, "Invest half the cash.")
  ```
- **Stacking servers:** nest many with `AsyncExitStack` (each `MCPServerStdio` is an async context).
  Mix your own servers with third-party ones (memory, web fetch/search, push).
- **Agents as tools:** `agent.as_tool()` lets a Trader embed a Researcher agent - hierarchical composition.
- The course capstone is an autonomous **trading floor**: an `accounts` MCP server, a market-data
  server and a push server, plus four trader agents (Warren / George / Ray / Cathie) that loop on a
  timer, research, trade, and even call `change_strategy()` - all watched in a Gradio UI.

**Built:** a mini **trading floor** - the capstone architecture. Two FastMCP servers:
`accounts_server.py` (`get_balance` / `buy_shares` + an `accounts://report` resource) and
`market_server.py` (`get_price` + a `market://prices` resource). `trading_floor.py` runs multiple
trader agents concurrently (`asyncio.gather`); each is an Agents-SDK agent that **stacks both MCP
servers** via `AsyncExitStack`, looks up prices from the market and records trades through its
account. The full course version adds a push server and a Gradio dashboard; same architecture.

## Distilled learning

**ELI5:** MCP is a USB port for agent tools. Instead of soldering each tool into every agent, you
put your tools behind a little "server" with a standard plug; any agent can plug in and instantly
"see" them. The server says "here are my tools and read-only resources"; the agent picks them up
automatically. Now tools are shareable and reusable across agents and projects.

```python
# server side: declare tools/resources, then run over stdio
@mcp.tool()
def buy_shares(symbol: str, quantity: int) -> str: ...

# client side: the agent discovers them - no per-tool wiring
async with MCPServerStdio(params={"command": "uv", "args": ["run", "python", "accounts_server.py"]}) as s:
    agent = Agent(name="Trader", mcp_servers=[s])
```
