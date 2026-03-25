
````markdown
# Curiosity Break MCP

A tiny MCP server with 3 simple tools that do not need any API key.

## Tools

- `random_advice` → gives one random advice
- `xkcd_latest` → gets the latest XKCD comic
- `xkcd_by_number` → gets a specific XKCD comic by number



---

## Quick option: use the live URL

This MCP is already live here:

```text
https://curiosity-break-mcp.onrender.com/mcp
````

So anyone can connect to it from Cursor without running the server locally.

Example Cursor config:

```json
{
  "mcpServers": {
    "curiosity-break-live": {
      "url": "https://curiosity-break-mcp.onrender.com/mcp"
    }
  }
}
```

---

## Local setup

Open your terminal inside the project folder and run:

```bash
uv sync
```

This installs the dependencies.

---

## Test it locally without Cursor

To make sure everything works, run:

```bash
uv run python demo_client.py
```

This will:

* start the server
* connect to it
* list the tools
* call the tools for you

---

## Run locally with stdio

For Cursor or another MCP client running locally, start the server with:

```bash
uv run python server.py
```

It may look like nothing is happening.

That is normal.

This MCP server uses **stdio**, which means it waits quietly for a client like Cursor to connect to it.

So if it just sits there, that means it is working.

---

## Run locally with HTTP

You can also run it locally as an HTTP MCP server:

```bash
uv sync
uv run python server.py --streamable-http
```

The MCP endpoint will be:

```text
http://127.0.0.1:8000/mcp
```

### Open it in a browser

The `/mcp` path is for MCP clients like Cursor.

If you open it in a browser, it will not show a normal friendly page.

For a normal browser view, open:

```text
http://127.0.0.1:8000/
```

That shows a simple page with:

* the latest XKCD
* an optional comic lookup
* a random advice line

---

## Connect it to Cursor

### Option 1: use the live URL

Inside your project root, create:

```bash
.cursor/mcp.json
```

If the `.cursor` folder does not exist, create it first.

Then add:

```json
{
  "mcpServers": {
    "curiosity-break-live": {
      "url": "https://curiosity-break-mcp.onrender.com/mcp"
    }
  }
}
```

---

### Option 2: use your local HTTP server

If you are running the server locally with `--streamable-http`, use:

```json
{
  "mcpServers": {
    "curiosity-break-http": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

---

### Restart Cursor

Close Cursor fully and open it again.

---

### Check MCP in Cursor

In Cursor:

* open **Settings**
* search for **MCP**
* look for **curiosity-break-live** or **curiosity-break-http**

Enable it if needed.

---

### Test in Cursor chat

Try prompts like:

* `Use the curiosity-break MCP and call xkcd_latest`
* `Use curiosity-break to get random_advice`
* `Call xkcd_by_number with 303`

---

## Notes

* Use the **live URL** if you want the simplest setup
* Use **stdio** if you want to learn how local MCP servers work
* Use **local HTTP** if you want to test remote-style MCP on your own machine

---

## Credits

* Advice Slip API
* XKCD JSON API

