# Trading floor simulation with 4 agents - added Anthropic and Gemini models

Overall setup & changes in this version
	• Agents setup:
		○ Two primary agent roles: Trader and Researcher.
		○ Researcher uses Brave Search MCP, fetch, and LibSQL memory.
		○ Trader executes trades using Accounts, Push notifications, and Market MCP (Polygon or fallback).
		○ Both share entity memory across MCP servers.
        ○ 4 Agents configured - 2 using GPT mini models, the other 2 using Claude and Gemini
	• Shim Clients:
		○ Anthropic (Claude): openai_compat_anthropic.py provides OpenAI-compatible wrapper over AsyncAnthropic.
		○ Gemini (Google): openai_compat_gemini.py provides similar wrapper with retry logic.
		○ Both shims translate chat.completions.create / responses.create into native API calls, then build true OpenAI ChatCompletion objects so the Agents SDK runs unchanged.
	• traders.py:
		○ get_model() → always returns a string (safe for serialization).
		○ instantiate_model_from_name() → instantiates correct runtime wrapper (OpenAIChatCompletionsModel with shim or async clients).
		○ Trader.run_agent() calls instantiation just before Runner.run(...).
		○ get_researcher_tool() now also uses instantiation, fixing prior 400 errors in Researcher.
	• templates.py:
		○ Prompt tuning - enforce budgets
		○ Clear termination instructions.

Trader & Researcher Instructions
	• Researcher (templates.py):
		○ Searches broadly across financial news.
		○ Uses knowledge graph to persist/retrieve entities, stocks, and URLs.
		○ Now explicitly capped: “Do at most 2–3 focused searches, retry once on failure, then stop and summarize.”
	• Trader (templates.py):
		○ Executes trades based on Researcher input.
		○ Uses tools for price data, fundamentals, ETFs for diversification.
		○ After trading: “Send a single push notification summary and STOP (no iterative refinements).”
		○ Push notifications must always include trader name.

Token/Temperature Strategy
	• Researcher:
		○ Higher max_tokens (2048) and moderate temperature (0.5).
		○ Broader, exploratory output.
	• Trader:
		○ Lower max_tokens (1024) and lower temperature (0.3).
		○ Precise, deterministic execution.

Error Fixes & Improvements
	• Error 400 (model not found / empty content):
		○ Caused by wrong model strings or empty messages.
		○ Fixed by stripping query params, skipping empty messages, and using instantiated shim for researcher.
	• Error 500 (Gemini internal error):
		○ Fixed with retry wrapper (2–3 attempts, exponential backoff).
		○ Implemented only in Gemini shim, but same logic could apply to Anthropic transient failures.
	• Tuple / NotGiven serialization issues:
		○ Fixed by returning real ChatCompletion Pydantic objects from shim (ChatCompletion.model_validate).
		○ _is_given helper filters out NotGiven and None.
	• Max_turns exceeded error for both Trader & Researcher, caused Researcher to loop for Claude:
		○ Prompt tuning - improve Trader and Researcher instrucutions in templates.py.
		○ If any tool fails twice or hits a step limit, summarize and stop (don’t keep searching).
		○ Looping was not seen in GPT/Gemini as they tended to finalize earlier and don’t re-call tools after non-fatal errors as aggressively as Claude


## Files changed from the lab
- `traders.py`: Updated as described above
- `trading_floor.py`: Updated for models
- `templates.py`: Updated instructions phrased to nudge Anthropic models to prefer tool use (Brave/fetch/market) and to avoid guessing.
- `app.py` : Updated for number of lines of logs and transactions
## Files added
- `openai_compat_anthropic.py` :  OpenAI-compatible wrapper over AsyncAnthropic.
- `openai_compat_gemini.py` :  OpenAI-compatible wrapper for Gemini with retry logic.
- `testClaude_tools_minimal.py` : Unit test script for Claude adapter
- `testGeminiShim.py` : Unit test script for Gemini adapter 
- `healthcheck.py` : Sanity check that pings Anthropic and Gemini with a simple query to check model is
		○ reachable?
		○ returns a valid ChatCompletion.
- `query_logs.ipynb` : utility script to query logs for an agent and display or write to txt/csv file in /report folder

## Files unchanged (includes remainining files from the lab to enable running the application from the CC folder)
- 'util.py'
- 'accounts.py'
- 'accounts_client.py'
- 'accounts_server.py'
- 'push_server.py'
- 'database.py'
- 'market_server.py'
- 'market.py'
- 'mcp_params.py'
- 'tracers.py'
- 'reset.py'


## Prereqs
- `uv` available on your PATH
- The following keys are defined in your .env
    OPENAI_API_KEY=sk-proj-....
    GOOGLE_API_KEY=AI....
    GEMINI_API_KEY=AI....
    ANTHROPIC_API_KEY=sk-ant-....
    PUSHOVER_USER=u1....
    PUSHOVER_TOKEN=ag....
    BRAVE_API_KEY=BS....
    POLYGON_API_KEY=iO....
    USE_MANY_MODELS=true
    RUN_EVERY_N_MINUTES=60
    RUN_EVEN_WHEN_MARKET_IS_CLOSED=True

## Execution
```bash
cd 6_mcp/community_contributions/trading_simulation_using_claude_gemini
uv run reset.py (to reset accounts in DB)
uv run healthcheck.py (to test connectivity and responses from Anthropic and Gemini)
uv run app.py (to trigger UI)
uv run trading_floor.py (to start trading)



