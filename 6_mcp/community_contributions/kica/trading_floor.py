import asyncio
import os

from agents import add_trace_processor
from crypto_tracers import LogTracer
from dotenv import load_dotenv
from traders import Trader

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]
model_name = os.getenv("CRYPTO_TRADER_MODEL", "gpt-4o-mini")
short_model_names = [model_name] * 4


def create_traders():
    return [
        Trader(name, lastname, model_name)
        for name, lastname in zip(names, lastnames)
    ]


async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    traders = create_traders()
    while True:
        await asyncio.gather(*[t.run() for t in traders])
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Crypto floor: every {RUN_EVERY_N_MINUTES} min (24/7), model={model_name}")
    asyncio.run(run_every_n_minutes())
