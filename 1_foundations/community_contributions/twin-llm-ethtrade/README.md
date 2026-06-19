# Twin-LLM ETH Trader

A Python/Jupyter project that:
- Fetches ETH daily OHLCV data
- Computes technical indicators (EMA, RSI, ATR, highs/lows)
- Uses two LLM agents:
  - **Analyst** → proposes BUY / SELL / HOLD
  - **Auditor** → approves or revises the call
- Outputs final structured JSON signals

⚠️ **Educational use only. Not financial advice.**

## Quickstart
```bash
uv add openai yfinance pandas numpy
cp .env.example .env   # add your OpenAI API key
uv run python eth_dual_llm_signal.py
