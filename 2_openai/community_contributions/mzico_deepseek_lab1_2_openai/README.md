# Week 2 Lab 1 — OpenAI Agents SDK with DeepSeek

Community contribution: same flow as the course `2_openai/1_lab1.ipynb`, but the model runs on **DeepSeek** via the OpenAI-compatible API (`OpenAIProvider` + `RunConfig`), using **`deepseek-chat`**.

## Requirements

- Course environment with `agents` (OpenAI Agents SDK), `openai`, `python-dotenv`
- A **DeepSeek** API key ([platform.deepseek.com](https://platform.deepseek.com/api_keys))

## Environment

Set `DEEPSEEK_API_KEY` (see `.env.example`). The notebook searches for `.env` in the current directory, one level up, and two levels up (so **`agents/.env`** is found even when this notebook is opened from `community_contributions/...`).

Do not commit real keys; use `.env` locally and keep it gitignored.

## How to run

1. Activate the course virtualenv (or use `uv run`) from the repo as usual.
2. Open `1_lab1_deepseek.ipynb` in Jupyter / VS Code.
3. Run cells in order (imports → env + provider → agent → `Runner.run`).

## Notes

- `use_responses=False` on `OpenAIProvider` is required: DeepSeek supports Chat Completions, not OpenAI’s Responses API.
- OpenAI Platform **traces** (`https://platform.openai.com/traces`) only apply if you use OpenAI tracing with an `OPENAI_API_KEY`; the model call itself uses DeepSeek.
