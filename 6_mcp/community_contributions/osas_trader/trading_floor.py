from traders import TraderAgent
from typing import List
import asyncio
from tracers import LogTracer
from agents import add_trace_processor
from market import is_market_open
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

# Trader personas
names = ["Alex", "Morgan", "Sam", "Jordan"]
lastnames = ["Fundamentals", "Momentum", "Contrarian", "Macro"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
    ]
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini"]
else:
    model_names = ["gpt-4.1-mini"] * 4
    short_model_names = ["GPT 4.1 Mini"] * 4


def create_trader_agents() -> List[TraderAgent]:
    return [
        TraderAgent(name, lastname, model_name)
        for name, lastname, model_name in zip(names, lastnames, model_names)
    ]


async def run_every_n_minutes() -> None:
    add_trace_processor(LogTracer())
    traders = create_trader_agents()
    print(f"Trading floor started — running every {RUN_EVERY_N_MINUTES} minutes")
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            print("Market is open — running all traders")
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Market is closed — skipping run")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(run_every_n_minutes())
