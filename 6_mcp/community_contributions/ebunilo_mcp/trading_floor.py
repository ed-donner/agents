import asyncio
import logging
import os

from dotenv import load_dotenv

from market import is_crypto_market_hours
from traders import Trader
from tracers import LogTracer
from agents import add_trace_processor

load_dotenv(override=True)

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "true").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

# Personas from trading_personas.md (Changpeng, Arthur, Willy, Michael Saylor)
names = ["Changpeng", "Arthur", "Willy", "Michael"]
lastnames = ["Zhao", "Hayes", "Woo", "Saylor"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gpt-4o-mini",
        "gpt-4.1-mini",
    ]
    short_model_names = [
        "GPT 4.1 Mini",
        "DeepSeek V3",
        "GPT 4o mini",
        "GPT 4.1 Mini",
    ]
else:
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4


def create_traders() -> list[Trader]:
    return [
        Trader(name, lastname, model_name)
        for name, lastname, model_name in zip(names, lastnames, model_names)
    ]


async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    traders = create_traders()
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_crypto_market_hours():
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Skipping run (scheduler gate)")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Crypto spot scheduler: every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
