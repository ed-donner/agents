import asyncio
from dotenv import load_dotenv
import os
from orchestrator import OrchestratorAgent

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
    ]
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini"]
else:
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4


async def run_trading_floor():
    """
    Main entry point - runs trading floor with orchestrator pattern.
    
    Uses shared MCP servers across all traders for optimal resource utilization.
    Reduces subprocess overhead by ~75% compared to legacy implementation.
    """
    print("Running with orchestrator (shared MCP servers)", flush=True)
    
    trader_configs = list(zip(names, lastnames, model_names))
    
    async with OrchestratorAgent(trader_configs) as orchestrator:
        await orchestrator.run_forever()


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes", flush=True)
    asyncio.run(run_trading_floor())
