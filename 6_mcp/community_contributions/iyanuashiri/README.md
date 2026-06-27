# Frankfurter MCP — Currency Conversion Server & Client

A Model Context Protocol (MCP) server and client for live currency conversion using the [Frankfurter API](https://www.frankfurter.dev/v1/) (ECB rates, no API key needed).

---

## Files

- `server.py` — MCP server exposing currency tools via stdio
- `client.py` — MCP client that connects to the server and calls its tools

---

## Tools

| Tool | Description |
|---|---|
| `convert_currency` | Convert an amount from one currency to another |
| `get_exchange_rate` | Get the mid-market rate between two currencies |
| `list_supported_currencies` | List all ISO 4217 codes supported by Frankfurter |

---

## Usage

### Run the server (stdio, for MCP clients like Claude Desktop / Cursor)

```bash
uv run server.py
```

### Run the client demo

```bash
uv run client.py
```

This will list available tools, print supported currencies, and run a couple of sample conversions.

### Use the client in your own code

```python
import asyncio
from client import convert_currency, get_exchange_rate, list_supported_currencies

async def main():
    print(await get_exchange_rate("USD", "EUR"))
    print(await convert_currency(250, "GBP", "JPY"))
    print(await list_supported_currencies())

asyncio.run(main())
```

---

## Connecting to Claude Desktop / Cursor

Add this to your MCP config (`mcp.json`):

```json
{
  "mcpServers": {
    "frankfurter": {
      "command": "uv",
      "args": ["run", "/path/to/server.py"]
    }
  }
}
```

Replace `/path/to/server.py` with the absolute path to `server.py`.

---

## Requirements

- Python 3.10+
- `uv` ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- Dependencies: `httpx`, `mcp[cli]`

Install deps:

```bash
uv pip install httpx "mcp[cli]"
```

---

## Notes

- Rates are sourced from the European Central Bank (ECB) via Frankfurter — updated on business days.
- No API key required.
- Currency codes must be valid ISO 4217 three-letter codes (e.g. `USD`, `EUR`, `NGN`).
