# DebateEngine Crew

A CrewAI-powered courtroom debate simulation with AI model performance tracking and multiple debate scenarios.

## Available Debate Cases

1. **AI Hiring Discrimination** (default)
   - Motion: AI hiring system liability under Title VII
   - Focus: Algorithmic bias and employment discrimination

2. **AI Copyright Infringement**
   - Motion: AI-generated artwork copyright infringement
   - Focus: Training data usage and originality

3. **Autonomous Vehicle Liability**
   - Motion: Self-driving car manufacturer strict liability
   - Focus: Product liability and autonomous systems

4. **AI Content Moderation**
   - Motion: AI moderation violates First Amendment
   - Focus: Free speech and algorithmic censorship

## Running the Project

```bash
# From the project folder
cd 3_crew/debate_engine

# First-time setup
uv sync

# Run a case (default = 1)
uv run python -m debate_engine.main run 1
uv run python -m debate_engine.main run 2
uv run python -m debate_engine.main run 3
uv run python -m debate_engine.main run 4

# Backwards compatible
uv run python -m debate_engine.main 2

# View historical rankings (no new run)
uv run python -m debate_engine.main rankings

# Train the crew (n_iterations, output file, optional case_number)
uv run python -m debate_engine.main train 5 training.pkl 2
```

If you want to run with plain `python` (without `uv`), you must include `src/` on `PYTHONPATH`:

```powershell
cd 3_crew/debate_engine
$env:PYTHONPATH = "src"
python -m debate_engine.main run 2
python -m debate_engine.main rankings
```

## Models (defaults to OpenAI)

CrewAI supports many providers via LiteLLM routing. **This project defaults to OpenAI models** (most stable).

- **OpenAI**: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`
- **Groq / Google / DeepSeek**: supported, but disabled by default in `main.py` because of quota/rate-limit issues.
  - To opt in, set one or more of: `INCLUDE_GROQ_MODELS=true`, `INCLUDE_GOOGLE_MODELS=true`, `INCLUDE_DEEPSEEK_MODELS=true`

Set the required API keys in your environment (or a `.env` file if you use one):

- **`.env` support**: the app will automatically load `3_crew/debate_engine/.env` if it exists.
- **OpenAI**: `OPENAI_API_KEY`
- **Groq**: `GROQ_API_KEY`
- **Google**: `GOOGLE_API_KEY`
- **DeepSeek**: `DEEPSEEK_API_KEY`

Run with custom models:

```bash
# Set prosecutor/defense directly
uv run python -m debate_engine.main run 1 ^
  --prosecutor-model "openai/gpt-4o-mini" ^
  --defense-model "deepseek/deepseek-chat" ^
  --judge-model "google/gemini-2.0-flash" ^
  --evidence-analyst-model "groq/llama-3.1-70b-versatile" ^
  --fact-checker-model "openai/gpt-4o-mini"

# Or provide a pool (prosecutor/defense will be sampled randomly)
uv run python -m debate_engine.main run 1 ^
  --model-pool "openai/gpt-4o-mini,deepseek/deepseek-chat,google/gemini-2.0-flash"
```

## Understanding Your Crew

The DebateEngine Crew simulates a courtroom debate with specialized AI agents:

- **Prosecutor** (GPT-4o-mini): Builds legal arguments for plaintiff/prosecution
- **Defense** (GPT-3.5-Turbo): Counters with defense arguments
- **Evidence Analyst** (GPT-4): Extracts and analyzes case facts
- **Judge** (GPT-4o): Evaluates arguments and delivers verdict
- **Fact Checker** (GPT-4o-mini): Verifies claims and flags inconsistencies

## Performance Tracking

The system automatically tracks debate outcomes and ranks AI models based on:
- Win rate across multiple cases
- Average debate scores (logic, evidence, rebuttal, clarity)
- Historical performance comparison

Results are saved in `outputs/debate_results.json` for analysis.

## Support

For support, questions, or feedback regarding the DebateEngine Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
