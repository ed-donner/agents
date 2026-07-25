# Pointing this day at a different model

ADK talks to Gemini natively. To run it against any OpenAI-compatible endpoint instead (OpenAI, OpenRouter, a local server, and so on), ADK routes through LiteLLM.

Install the extra in this folder:

```bash
uv add "google-adk[extensions]"
```

Then wrap the model. In `task_worker/agent.py`, swap the model string for a `LiteLlm` instance:

```python
from google.adk.models.lite_llm import LiteLlm

root_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-5.4-mini"),   # any LiteLLM model string
    name="task_worker",
    description="Works one task from the SQLite board using its files.",
    instruction=...,        # unchanged
    tools=[show_todos, plan_steps, complete_task, filesystem],
)
```

The `openai/` prefix tells LiteLLM to use the OpenAI chat protocol. With `OPENAI_API_KEY` in your `.env`, `openai/gpt-5.4-mini` works with no further configuration.

For a custom endpoint such as OpenRouter, pass `api_base` and `api_key`:

```python
import os

model = LiteLlm(
    model="openai/gpt-5.4-mini",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
```

Everything else in the day stays exactly the same. The tools, the filesystem MCP server, and the board are all model-agnostic, so only the one model line changes.
