# Pointing this day at a different model

This day has two workers, `strands_worker.py` and `pydantic_worker.py`. Both default to OpenAI's `gpt-5.4-mini`, read from the `WORKER_MODEL` environment variable, so the quickest swap to another OpenAI model is to set it for a run, for example `WORKER_MODEL=gpt-5.4 uv run strands_worker.py`. To use a different provider or any OpenAI-compatible endpoint (OpenRouter, a local server, and so on), each framework reaches its model in one place; change it in whichever worker you are running.

## Strands

Strands talks to several providers through dedicated model classes, and this day uses `OpenAIModel`. Add a `base_url` to `client_args` (the arguments Strands hands straight to the OpenAI client) to point at a different endpoint, and set `model_id` to the model that endpoint serves:

```python
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    client_args={
        "api_key": os.environ["OPENROUTER_API_KEY"],  # any non-empty string for a local server
        "base_url": "https://openrouter.ai/api/v1",   # or http://localhost:11434/v1 for Ollama
    },
    model_id="gpt-5.4-mini",
)
```

With no `base_url`, `OpenAIModel` calls OpenAI directly using `OPENAI_API_KEY`. Nothing else in `strands_worker.py` changes.

## Pydantic AI

Pydantic AI picks a provider with a `provider:model` string, and this day uses `openai-chat:gpt-5.4-mini` (the explicit Chat Completions prefix). To reach a different endpoint, build an `OpenAIChatModel` around an `OpenAIProvider` that carries the `base_url` and `api_key`, then hand that model to the agent in place of the string:

```python
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    "gpt-5.4-mini",
    provider=OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",      # or http://localhost:11434/v1 for Ollama
        api_key=os.environ["OPENROUTER_API_KEY"],
    ),
)

worker = Agent(model, instructions=INSTRUCTIONS, tools=[show_todos, plan_steps, complete_task], toolsets=[filesystem])
```

The class is `OpenAIChatModel`, not the older `OpenAIModel` name. You can also keep the `openai-chat:gpt-5.4-mini` string and just set `OPENAI_BASE_URL` and `OPENAI_API_KEY` in your `.env`.

Everything else in the day stays exactly the same. The board tools, the filesystem MCP server, and the board are all model-agnostic, so only the one model line changes.
