# Week 6 Lab 1: MCP on free Gemini, searching for Hakka Noodles

This is my version of the Week 6 Lab 1 MCP agent. It runs on the free Gemini API instead of OpenAI, and it looks for my favourite dish, Hakka Noodles, instead of Banoffee Pie.

## What I changed

- **Gemini instead of OpenAI.** The OpenAI Agents SDK points at Gemini's OpenAI-compatible endpoint and uses `gemini-3.5-flash-lite`. Tracing is off, because traces upload to OpenAI.
- **Search with DuckDuckGo first.** In my first runs the agent made up recipe URLs, and each one came back as "page not found". It hit `MaxTurnsExceeded` before any page loaded. Now the instructions tell it never to guess a URL. It starts at `https://html.duckduckgo.com/html/?q=...`, opens a real result link, and goes back to the next result if a page is a 404.
- **Stop early.** As soon as it has the ingredients and steps, it stops browsing and writes the file. `max_turns` is now 30.
- **Windows fix.** The server's stderr goes to the null device so `MCPServerStdio` starts inside a Windows Jupyter kernel.

## Files

- `hakka_noodles_mcp_lab.ipynb`: the lab notebook, with outputs cleared.
- `noodles.md`: what the agent wrote into its sandbox. The recipe came from Swasthi's Recipes.

## Running it

Put `GEMINIAI_API_KEY` in your `.env`. You also need Node 22+ and Chrome for the Playwright and filesystem MCP servers.

It took me many tries, but I finally got my favourite dish.
