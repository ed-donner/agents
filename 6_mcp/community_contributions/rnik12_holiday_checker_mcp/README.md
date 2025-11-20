# Holiday Checker MCP

An MCP server that answers: “Are there public holidays in X between date A and date B?”
- **Zero API keys** (uses `python-holidays`)
- A tiny **Agent** wired with the OpenAI Agents SDK
- A **Gradio UI** with Chat + Form tabs

## Install

```bash
uv add gradio holidays mcp openai-agents
````

(Agents SDK + MCP deps already exist in Week 6 labs.)

## Quick demo (chat)

```bash
cd 6_mcp/community_contributions/rnik12_holiday_checker_mcp
OPENAI_API_KEY=... uv run gradio_ui.py
```

Open the link; ask:

> Are there holidays in India between 2025-12-20 and 2026-02-05?