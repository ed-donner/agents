## Trading with shorting

This is based on the trading example in the course. It is a demonstration of 'paper' trading of equities with agents and MCP tools. It is not meant for live trading.
There are 4 traders with different trading strategies and possibly using different LLMs.

Its behaviour is influenced by these .env values

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)

RESET_TRADERS = os.getenv("RESET_TRADERS", "true").strip().lower() == "true"

when true the 4 traders are reset to their starting values.

USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

when true these models will be used, otherwise they all use gpt-4.1-mini
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash",
        "grok-3-mini-beta",
    ]


First start trading_floor from the trading_with_short folder -  uv run accounts.py

Then the gradio interface - uv run app.py
