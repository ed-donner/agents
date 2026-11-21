# Digital Twin with Gemini Evaluator (Lab 4, Exercise 4)

Adds the evaluator-optimizer pattern to the Lab 4 digital twin.

- `run_twin()`: OpenAI chat with tool-calling loop
- `evaluate()`: Gemini (via OpenAI-compatible endpoint) checks each reply with structured output
- `rerun()`: retries with the evaluator's feedback if the reply is rejected
- Prompt rules: no price quotes, confirm follow-up when an email is recorded, and only record unknown questions that are genuinely not in the context

## Setup
1. Add your own `linkedin.pdf` and edit `summary.txt`
2. Set env vars: OPENAI_API_KEY, GOOGLE_API_KEY, PUSHOVER_USER, PUSHOVER_TOKEN
3. Run: `uv run app.py`
