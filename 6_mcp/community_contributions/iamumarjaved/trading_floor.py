from src.agents.traders import Trader
from src.agents.risk_manager import RiskManager
from src.agents.news_sentinel import NewsSentinel
from typing import List
import asyncio
from src.utils.tracers import LogTracer
from agents import add_trace_processor
from src.utils.market import is_market_open
from dotenv import load_dotenv
import os

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
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o",
    ]
    short_model_names = ["GPT 4o Mini", "GPT 4o", "GPT 4o Mini", "GPT 4o"]
else:
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4

def create_traders() -> List[Trader]:
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders

async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    traders = create_traders()
    risk_manager = RiskManager(names, model_name="gpt-4o-mini")
    news_sentinel = NewsSentinel(names, model_name="gpt-4o-mini")

    iteration = 0
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            print(f"\n{'='*60}")
            print(f"Trading Floor - Iteration {iteration + 1}")
            print(f"{'='*60}\n")

            await asyncio.gather(*[trader.run() for trader in traders])

            print(f"\nRunning Risk Manager Assessment...")
            await risk_manager.run()

            print(f"\nRunning News Sentinel Monitoring...")
            await news_sentinel.run()

            iteration += 1
        else:
            print("Market is closed, skipping run")

        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    print(f"Risk Manager will assess portfolios after each trading cycle")
    print(f"News Sentinel will monitor holdings for breaking news")
    asyncio.run(run_every_n_minutes())
