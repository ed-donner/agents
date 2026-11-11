# Week 6 Lab 4 Trading Floor on free models only

**Author:** Paresh Tahiliani

This is the Week 6 trading floor (`uv run app.py` and `backend.trading_floor`) changed so it runs
without paying for anything. There is no OpenAI key, no DeepSeek or Grok key and no Pushover account.
Each of the four traders runs on a different free model:

| Trader | Model | Provider |
|---|---|---|
| Warren | `gemini-3.5-flash` | Google Gemini (free tier) |
| George | `openai/gpt-oss-120b` | Groq (free tier) |
| Ray | `qwen/qwen3.8-27b` | Groq (free tier) |
| Cathie | `llama3.2` | Ollama (local, no key) |

The rest of the stack is free too:
- **Web search:** Tavily's free tier.
- **Push notifications:** [ntfy.sh](https://ntfy.sh) instead of Pushover.
- **Prices:** without a Massive key, the course's simulated prices.

## What changed

All three files replace the ones with the same name in `6_mcp/backend/`.

- **`traders.py`**
  - Model ids starting with `groq/` go to Groq's OpenAI-compatible endpoint, and ids starting
    with `ollama/` go to local Ollama (`OLLAMA_BASE_URL`, default `http://localhost:11434/v1`).
    The prefix is needed because Groq ids such as `openai/gpt-oss-120b` contain a `/`, which the
    original code sends to OpenRouter.
  - API clients are created only when a model needs them, so you only need keys for the
    providers you use.
- **`trading_floor.py`**
  - The models in the table above, with `USE_MANY_MODELS` on by default. Set
    `USE_MANY_MODELS=false` to put every trader on `gemini-3.5-flash-lite`.
  - `set_trace_processors([LogTracer()])` replaces the default OpenAI trace exporter, which
    needs an OpenAI key. The dashboard logs still work.
- **`push_server.py`**
  - The `push` tool posts to `https://ntfy.sh/<NTFY_TOPIC>`. Install the ntfy phone app, subscribe
    to a topic name that is hard to guess, and the traders' notifications arrive there.

## Setup

1. Copy the `backend/` files from this folder over `6_mcp/backend/`.
2. Add these to `.env`:
   ```
   GOOGLE_API_KEY=...        # https://aistudio.google.com/apikey
   GROQ_API_KEY=...          # https://console.groq.com/keys
   TAVILY_API_KEY=...        # https://app.tavily.com
   NTFY_TOPIC=...            # your own hard-to-guess topic name
   RUN_EVEN_WHEN_MARKET_IS_CLOSED=true   # optional, for testing outside market hours
   ```
3. Install [Ollama](https://ollama.com), then run `ollama pull llama3.2`.
4. From `6_mcp/`, run the traders in one terminal and the dashboard in another:
   ```
   uv run -m backend.trading_floor
   uv run app.py
   ```

## Known limits

- **Groq's free tier** has low tokens-per-minute limits, and each trader's prompt with all its MCP
  tools is large. If George or Ray hit rate limits, use `groq/openai/gpt-oss-20b` or
  `gemini-3.5-flash-lite` for them in `trading_floor.py`.
- **Llama 3.2** is a 3B model and may call the many tools badly. Ollama's default context window
  may also be too small. Any local model that supports tool calling can replace it, for example
  `ollama/qwen3:8b` if your machine can run it.
- **Model names change:** the Groq and Gemini model ids were available in October 2026. Check
  each provider's model list if one stops working.
