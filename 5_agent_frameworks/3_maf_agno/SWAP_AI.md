# Pointing this day at a different model

This day has two workers, `maf_worker.py` and `agno_worker.py`. Both default to OpenAI's `gpt-5.4-mini`, read from the `WORKER_MODEL` environment variable, so the quickest swap to another OpenAI model is to set it for a run, for example `WORKER_MODEL=gpt-5.4 uv run maf_worker.py`. To use a different provider or any OpenAI-compatible endpoint (OpenRouter, a local server, and so on), each framework reaches its model in one place; change it in whichever worker you are running.

## Microsoft Agent Framework

MAF reaches the model through a chat client, and this day uses `OpenAIChatClient`. Its constructor takes `model`, `base_url` and `api_key` directly, so pointing it at a different endpoint is a one-liner:

```python
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(
    model="gpt-5.4-mini",
    base_url="https://openrouter.ai/api/v1",      # or http://localhost:11434/v1 for Ollama
    api_key=os.environ["OPENROUTER_API_KEY"],     # any non-empty string for a local server
)
```

With no `base_url`, the client reads `OPENAI_API_KEY` from your `.env` and calls OpenAI directly. Nothing else in `maf_worker.py` changes.

## Agno

Agno calls OpenAI through `OpenAIChat`; for any other OpenAI-compatible endpoint it ships `OpenAILike`, which takes the same `id` plus a `base_url` and `api_key`:

```python
from agno.models.openai.like import OpenAILike

model = OpenAILike(
    id="gpt-5.4-mini",
    base_url="https://openrouter.ai/api/v1",      # or http://localhost:11434/v1 for Ollama
    api_key=os.environ["OPENROUTER_API_KEY"],     # any non-empty string for a local server
)
```

`OpenAIChat` accepts `base_url` and `api_key` too, but `OpenAILike` is the documented choice for non-OpenAI endpoints. Swap `OpenAIChat(id=MODEL)` for this, and the rest of `agno_worker.py` is unchanged.

Everything else in the day stays exactly the same. The board tools, the filesystem MCP server, and the board are all model-agnostic, so only the one model line changes.
