# Week 6 Primer — Model Context Protocol (MCP)

> Read before the labs. Every framework so far had its *own* way to define tools.
> MCP is the **open standard** that decouples tools from frameworks — "USB-C for
> AI tools." This is the most strategically important week for staying current.

---

## The one mental model

Until now, a tool was tied to a framework: a `@function_tool` works in the OpenAI SDK, a `BaseTool` in CrewAI, etc. Rewrite the tool to switch frameworks. **MCP breaks that coupling** by defining a *protocol* between an agent (client) and a tool **server**:

```
  ┌──────────────┐         MCP protocol          ┌──────────────────┐
  │  ANY agent   │  ◀───────────────────────────▶│   tool SERVER    │
  │ (client)     │   list_tools() / call_tool()  │  (your code,     │
  │ OpenAI/Crew/ │   read_resource()             │   hidden behind  │
  │ AutoGen/...  │                               │   the protocol)  │
  └──────────────┘                               └──────────────────┘
   discovers tools at runtime          implementation (SQLite, APIs,
   — doesn't hardcode them              files) fully abstracted away
```

The two moves that matter:
1. **Discovery at runtime** — the agent calls `list_tools()` and learns what the server offers *dynamically*, instead of hardcoding schemas.
2. **Implementation hiding** — the server exposes tools and *resources*; the agent never knows if it's backed by SQLite, a web API, or a file. Swap the backend without touching the agent.

Write a tool once as an MCP server → any MCP-compatible agent can use it. That's the whole pitch.

---

## Key concepts, precisely

**Client vs server.** The *server* exposes tools/resources. The *client* (your agent's runtime) connects and consumes them. One agent can connect to *many* servers at once (`mcp_servers=[...]`).

**Transports.** `MCPServerStdio` spawns a server as a subprocess and talks over stdin/stdout — the common local pattern. Servers can also be remote (HTTP).

**Tools vs Resources.** *Tools* are callable functions (verbs). *Resources* are structured data endpoints the agent can read (nouns) — e.g., a document, a record set. Don't conflate them.

**Building a custom server (Lab 2)** — wrap existing Python (e.g., an accounts system) with the MCP SDK; your functions become discoverable tools. This is the skill that matters: *exposing your own systems to any agent*.

**Server taxonomy (Lab 3)** — local-only (e.g., a memory graph DB), local-with-web-service (Brave Search, Polygon.io — local process calling a remote API), and remote (cloud-hosted). Plus smart caching to respect rate limits.

**The Trading Floor capstone** — the course's most complex project. Multiple trader agents connect to three MCP servers (accounts, market, push). The architectural punchline: **each agent only knows the protocol; the SQLite/market-sim/push implementations are completely hidden.** That's MCP's value made concrete.

---

## What an interviewer is really testing

- *"What problem does MCP solve?"* → Tool portability and discovery. Before MCP, tools were re-implemented per framework; MCP lets you write a tool server once and plug any compatible agent into it, with runtime discovery and full implementation hiding. (Analogy: a universal driver/USB-C for AI tools.)
- *"MCP tool vs a direct function tool — trade-offs?"* → MCP adds portability, dynamic discovery, and decoupling at the cost of running a server process and protocol overhead. Direct tools are simpler for a single app but lock you to one framework.
- *"How does an agent know what an MCP server can do?"* → `list_tools()` at runtime — dynamic discovery, not a hardcoded schema. This is the line that shows you actually get MCP.

---

## Tradeoffs & gotchas

- **Operational overhead.** Each server is a process to run, monitor, and secure. For a one-off tool in a single app, a direct function tool is simpler. MCP pays off with reuse and multi-agent/multi-framework setups.
- **Security surface.** A server that exposes filesystem or shell access is a real risk — combine with sandboxing/allowlists (Week 7 Lab 5, Week 8). An MCP server is a trust boundary.
- **Windows subprocess issue.** Stdio server spawning has a known Windows problem — use WSL2 (per the README). Environmental, not conceptual, but it *will* block you.
- **Versioning & contracts.** Since discovery is dynamic, a server changing its tool signatures can silently break clients. Treat the tool surface as an API contract.

---

## Self-test

<details><summary>1. What two things does MCP decouple, and how?</summary>
Tools from frameworks (write once, any compatible agent can use it) and agents from implementations (server hides whether it's backed by SQLite/API/files). Done via a standard protocol with runtime discovery.</details>

<details><summary>2. Tools vs resources in MCP?</summary>
Tools are callable functions (verbs); resources are readable structured-data endpoints (nouns).</details>

<details><summary>3. How does an agent discover a server's capabilities?</summary>
By calling list_tools() at runtime — dynamic discovery rather than a hardcoded schema.</details>

<details><summary>4. In the Trading Floor capstone, what's the architectural punchline?</summary>
Agents know only the MCP protocol; the actual implementations (SQLite, market simulation, push service) are fully hidden behind the servers and can be swapped without touching the agents.</details>

---

**Labs:** `1` built-in servers + discovery → `2` build a custom server + resources → `3` server ecosystem + caching → Trading Floor capstone.

**Next:** [Week 7 Primer](../7_advanced/PRIMER.md) — make all of this production-grade.
