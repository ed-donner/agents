import asyncio
import os
import sys
from pathlib import Path
from typing import List

from agents import add_trace_processor
from dotenv import load_dotenv

_CONTRIB_DIR = Path(__file__).resolve().parent
if str(_CONTRIB_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTRIB_DIR))

ROOT_6_MCP = Path(__file__).resolve().parents[2]
if str(ROOT_6_MCP) not in sys.path:
    sys.path.append(str(ROOT_6_MCP))

from tracers import LogTracer
from market import is_market_open
from traders import Trader

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Growth"]

if USE_MANY_MODELS:
    model_names = [
        "llama-3.3-70b-versatile",
        "qwen-3-235b-a22b-instruct-2507",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
    ]
else:
    model_names = [os.getenv("TRADER_MODEL", "llama-3.3-70b-versatile")] * 4

# Show the actual configured model name on the UI.
short_model_names = model_names


def create_traders() -> List[Trader]:
    return [Trader(name, lastname, model_name) for name, lastname, model_name in zip(names, lastnames, model_names)]


async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    traders = create_traders()
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Market is closed, skipping run")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting US equities + crypto trader scheduler every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
