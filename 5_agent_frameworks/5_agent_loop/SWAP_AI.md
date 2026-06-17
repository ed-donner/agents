# Swapping the models

The agent loop uses two models: one for the Google ADK orchestrator agent, which leads the team, authors the look and the hub, and plays the games to check them, and one shared by the five workers that build the games. Both are set in one place, `config.py`:

```python
ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.5-flash")  # cheaper: gemini-3.1-flash-lite
WORKER_MODEL = os.environ.get("WORKER_MODEL", "gpt-5.5")  # cheaper: gpt-5.4-mini
```

The defaults are the larger models, for the best-looking arcade. To run cheaply, change the two strings to the lighter ones in the comments. You can also override either one for a single run without editing the file:

```bash
ORCHESTRATOR_MODEL=gemini-3.1-flash-lite WORKER_MODEL=gpt-5.4-mini uv run agent_loop.py
```

The orchestrator passes `WORKER_MODEL` to each worker through the environment, so every worker uses the model you choose here. Run a worker on its own (the Day 2 to 4 demo, with no arguments) and it falls back to its own committed model, so the standalone days are unaffected.

A worker speaks to whichever provider its framework points at. The workers here use OpenAI Chat Completions, so any OpenAI chat model id works in `WORKER_MODEL`. To reach a different provider, change the model client inside that worker exactly as its own day's `SWAP_AI` notes describe; the orchestrator does not need to know.

## The browser the QA agent uses

The check-the-work step is itself an agent. To judge a game, the orchestrator hands it to a short-lived QA agent that plays it in a browser. That browser comes through the Playwright MCP server, launched on demand with `npx @playwright/mcp` (no install step, like the filesystem MCP server you have used all week) and driving your system Google Chrome. A fresh QA agent per game keeps each browser session small and focused.

By default that Chrome window is visible so you can watch the agent play each game. Set `QA_HEADLESS=1` to run the checks without a window, which is handy on a headless or CI machine.

If Chrome or the MCP server is unavailable, the run still completes: `test_game` reports back that it could not reach the browser, the orchestrator moves on, and the finished site still opens for you to play.
