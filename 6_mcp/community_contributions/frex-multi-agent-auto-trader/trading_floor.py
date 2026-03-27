from traders import Trader, RiskManager
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


def create_traders() -> List[Trader]:
    return [
        Trader(name, lastname, model_name)
        for name, lastname, model_name in zip(names, lastnames, model_names)
    ]


def create_risk_managers() -> List[RiskManager]:
    """One Risk Manager per trader account, running independently."""
    return [
        RiskManager(name, model_name)
        for name, model_name in zip(names, model_names)
    ]


async def run_cycle(traders: List[Trader], risk_managers: List[RiskManager]):
    """
    Each cycle:
    1. Risk Managers run FIRST — they assess exposure and set/clear circuit breakers.
    2. Execution Traders run AFTER — they must check the circuit breaker before trading.
    Both groups run in parallel within their phase.
    """
    print("Phase 1: Risk assessment...")
    await asyncio.gather(*[rm.run() for rm in risk_managers])

    print("Phase 2: Execution trading...")
    await asyncio.gather(*[trader.run() for trader in traders])


async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    traders = create_traders()
    risk_managers = create_risk_managers()

    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await run_cycle(traders, risk_managers)
        else:
            print("Market is closed, skipping run")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
