# Repo onboarding MCP

Read-only **Model Context Protocol** tools for exploring a **local** repository, plus a minimal **OpenAI Agents SDK** client.



## LLM (OpenRouter only)

`agent_demo.py` uses the OpenAI Agents SDK with chat completions routed through **[OpenRouter](https://openrouter.ai/)** (OpenAI-compatible API). Set **`OPENROUTER_API_KEY`** (required). Optional: `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL` (default `openai/gpt-4o-mini`), `OPENROUTER_HTTP_REFERER`, `OPENROUTER_APP_TITLE`.

## Run the agent demo

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
export OPENROUTER_MODEL=openai/gpt-4o-mini   # optional

export REPO_ONBOARDING_ROOT=/absolute/path/to/a/repo   # optional; defaults to course `agents/` root when layout matches

uv run agent_demo.py "What are the main folders here and where should I start reading?"
```

You can pass a one-off question as CLI args; with no args, a default onboarding prompt is used.

## Run the MCP server alone (stdio)

Used automatically by the Agents SDK. For debugging:

```bash
export REPO_ONBOARDING_ROOT=/path/to/repo
uv run python server.py
# (stdio — connect with an MCP client)
```

## Safety

- All paths are resolved **under** `REPO_ONBOARDING_ROOT`; `..` and absolute escapes are rejected.
- Large/binary files are skipped or truncated; search skips `.git`, `node_modules`, `__pycache__`, common venv dirs.

