from traders import Trader
from accounts import Account
from typing import List
import asyncio
from tracers import LogTracer
from agents import add_trace_processor
from market import is_market_open
from dotenv import load_dotenv
import os
import templates

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

# 5 traders including Solisoma
names = ["Warren", "George", "Ray", "Cathie", "Solisoma"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto", "Sentiment"]

if USE_MANY_MODELS:
    model_names = [
        "gpt-4.1-mini",
        "deepseek-chat",
        "gemini-2.5-flash-preview-04-17",
        "grok-3-mini-beta",
        "gpt-4o-mini",  # Solisoma uses GPT
    ]
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini", "GPT 4o mini"]
else:
    model_names = ["gpt-4o-mini"] * 5
    short_model_names = ["GPT 4o mini"] * 5


def setup_solisoma():
    """Setup Solisoma account and custom strategy"""
    Account.get("Solisoma")

    # Override trader instructions
    original_trader_instructions = templates.trader_instructions
    
    def custom_trader_instructions(name):
        if name == "Solisoma":
            return """
            You are Solisoma, a sentiment-driven momentum trader.
            STRATEGY: Trade based on market sentiment and news momentum
            - ALWAYS use get_stock_sentiment(symbol) before ANY trade decision
            - Use analyze_overall_sentiment() to gauge market mood
            - Only buy stocks with BULLISH sentiment (strong positive news flow)
            - Sell if sentiment turns BEARISH
            - Stay cash in NEUTRAL/FEARFUL markets
            RULES:
            - Check sentiment FIRST, fundamentals second
            - Quick entries, quick exits (momentum trading)
            - Max 3 stocks at a time (concentrated bets)
            - Use get_market_news() to understand why sentiment shifted
            - Trade on momentum, not fundamentals
            """
        return original_trader_instructions(name)
    
    templates.trader_instructions = custom_trader_instructions


def create_traders() -> List[Trader]:
    """Create all 5 traders with sentiment MCP server"""
    setup_solisoma()
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    """Main trading loop for all 5 traders"""
    add_trace_processor(LogTracer())
    traders = create_traders()
    print(f"5 traders initialized: {names}")
    
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            print(f"\nRunning trading cycle for {len(traders)} traders...")
            await asyncio.gather(*[trader.run() for trader in traders])
            print("Trading cycle complete")
        else:
            print("Market is closed, skipping run")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    print(f"5 traders: {names}")
    asyncio.run(run_every_n_minutes())

