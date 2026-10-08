from .traders import Trader
from typing import List
import asyncio
from .tracers import LogTracer
from agents import set_trace_processors
from .market import is_market_open
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "true").strip().lower() == "true"

names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    # One trader per provider: Gemini and Groq use the keys in .env, Ollama runs locally
    model_names = [
        "gemini-3.5-flash",
        "groq/openai/gpt-oss-120b",
        "groq/qwen/qwen3.8-27b",
        "ollama/llama3.2",
    ]
    short_model_names = ["Gemini 3.5 Flash", "GPT-OSS 120B (Groq)", "Qwen3.8 27B (Groq)", "Llama 3.2 (Ollama)"]
else:
    model_names = ["gemini-3.5-flash-lite"] * 4
    short_model_names = ["Gemini 3.5 Flash Lite"] * 4


def create_traders() -> List[Trader]:
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    set_trace_processors([LogTracer()])  # replaces the default OpenAI trace exporter, which needs an OpenAI key
    traders = create_traders()
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Market is closed, skipping run")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
