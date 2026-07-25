from modules.traders import Trader
from modules.crypto_trader import CryptoTrader
from typing import List
import asyncio
from modules.tracers import LogTracer
from agents import add_trace_processor
from modules.market import is_market_open
from dotenv import load_dotenv
from modules.opportunity_scanner import OpportunityScanner
from modules.risk_manager_agent import RiskManager
from modules.portfolio_optimizer import PortfolioOptimizer
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

names = ["Warren", "George", "Ray", "Cathie", "Satoshi"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto", "Blockchain"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
        "gpt-4o-mini",
    ]

    short_model_names = [
        "GPT 4.1 Mini",
        "DeepSeek V3",
        "Gemini 2.5 Flash",
        "Grok 3 Mini",
        "GPT 4o Mini",
    ]

else:
    model_names = ["gpt-4o-mini"] * 5
    short_model_names = ["GPT 4o mini"] * 5


def create_traders() -> List[Trader]:
    traders = []

    for name, lastname, model_name in zip(names, lastnames, model_names):

        if name == "Satoshi":
            traders.append(CryptoTrader(name, lastname, model_name))
        else:
            traders.append(Trader(name, lastname, model_name))

    return traders


async def run_every_n_minutes():
    add_trace_processor(LogTracer())

    traders = create_traders()

    # Initialize additional agents
    scanner = OpportunityScanner()
    risk_manager = RiskManager(names)
    optimizer = PortfolioOptimizer(names)

    while True:

        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():

            # Scan market opportunities
            scanner.scan()

            # Run trader agents
            await asyncio.gather(*[trader.run() for trader in traders])

            # Evaluate portfolio risk
            risk_manager.evaluate()

            # Portfolio OPtimizer
            optimizer.optimize()

        else:
            print("Market is closed, skipping run")

        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
