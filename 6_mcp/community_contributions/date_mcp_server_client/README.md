# Date MCP Server + Client

A minimal Model Context Protocol (MCP) server that exposes a single tool `current_date` returning today's date in ISO format, and a matching client that lists tools and invokes it.

## Files
- `date_server.py`: MCP server exposing `current_date`
- `date_client.py`: Client helpers using stdio to connect via `uv`
- `date_tutorial.ipynb`: Walkthrough notebook to try it end-to-end

## Prereqs
- `uv` available on your PATH

## Quickstart
```bash
cd 6_mcp/community_contributions/date_mcp_server_client
uv run python - << 'PY'
import asyncio
from date_client import list_date_tools, call_date_tool
async def main():
    tools = await list_date_tools()
    print('Tools:', [t.name for t in tools])
    res = await call_date_tool('current_date')
    contents = getattr(res, 'content', None) or getattr(res, 'contents', None)
    if contents:
        vals = []
        for c in contents:
            vals.append(getattr(c, 'text', None) or getattr(c, 'value', None) or str(c))
        print('Result:', ' '.join(vals))
    else:
        print('Raw result:', res)
asyncio.run(main())
PY
```

You can also open the `date_tutorial.ipynb` notebook and run the cells.


