# Digital Twin with the OpenAI Agents SDK

A port of the Week 1 digital twin (`1_foundations/twin`) to the OpenAI Agents SDK, done as the exercise at the end of `2_openai/1_lab1.ipynb`.

## What changed compared to Week 1

| Week 1 | Agents SDK |
|---|---|
| Hand-written `while finish_reason == "tool_calls"` loop | `Runner.run(agent, ...)` |
| Large JSON schemas and a `tool_map` for each tool | `@function_tool` - the schema is generated from type hints and the docstring |
| `OpenAI` client | `AsyncOpenAI` through OpenRouter, wrapped in `OpenAIChatCompletionsModel` |

The notebook has two tools: `record_user_details` (records a visitor's email) and `record_unknown_question` (records a question the twin couldn't answer). Both send a Pushover notification. It also prints `record_user_details.params_json_schema` to show what the model sees.

Note: the SDK uses strict schemas, so every parameter is listed under `required`, even ones with Python defaults. The model must always supply `name` and `notes`.

## Setup

Add these to your `.env`: `OPENROUTER_API_KEY`, `OPENAI_API_KEY` (used only for tracing), `PUSHOVER_USER`, `PUSHOVER_TOKEN`.

Put your own `osama_linkedin.pdf` (rename the file in the notebook as needed) and `summary.txt` next to the notebook. They are not included in this folder because they hold personal data.
