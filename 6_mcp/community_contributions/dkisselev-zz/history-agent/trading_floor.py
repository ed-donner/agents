from traders import Trader
from typing import List
import asyncio
from tracers import LogTracer
from agents import add_trace_processor
from market import is_market_open
from dotenv import load_dotenv
import os
from datetime import datetime
from accounts import Account, INITIAL_BALANCE
from database import clear_simulation_date
from simulation import SimulationClock, HistoricalDataCache, init_simulation_cache

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"

# Simulation configuration
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").strip().lower() == "true"
SIMULATION_START = os.getenv("SIMULATION_START_DATE", "2024-01-01")
SIMULATION_END = os.getenv("SIMULATION_END_DATE", "2024-12-31")

# API rate limiting - Brave Search
TRADER_DELAY_SECONDS = int(os.getenv("TRADER_DELAY_SECONDS", "5"))

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
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    print("\n" + "="*80)
    print("TRADING FLOOR STARTING")
    print("="*80)
    print(f"Traders: {', '.join(names)}")
    print(f"Models: {', '.join(short_model_names)}")
    print(f"Run interval: {RUN_EVERY_N_MINUTES} minutes")
    print(f"Run when market closed: {RUN_EVEN_WHEN_MARKET_IS_CLOSED}")
    print("="*80 + "\n")
    
    add_trace_processor(LogTracer())
    traders = create_traders()
    run_count = 0
    
    while True:
        run_count += 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "-"*80)
        print(f"TRADING CYCLE #{run_count} - {current_time}")
        print("-"*80)
        
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            try:
                await asyncio.gather(*[trader.run() for trader in traders])
                print(f"Trading cycle #{run_count} completed")
            except Exception as e:
                print(f"Error in trading cycle #{run_count}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Market is closed, skipping run")
        
        next_run = datetime.fromtimestamp(datetime.now().timestamp() + RUN_EVERY_N_MINUTES * 60)
        print(f"\nNext run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sleeping for {RUN_EVERY_N_MINUTES} minutes...")
        print("-"*80 + "\n")
        
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


async def run_simulation():
    """Run historical simulation"""
    
    print("\n" + "="*80)
    print("HISTORICAL SIMULATION MODE")
    print("="*80)
    print(f"Period: {SIMULATION_START} to {SIMULATION_END}")
    print(f"Traders: {', '.join(names)}")
    print("="*80)
    
    # Initialize simulation clock and cache
    clock = SimulationClock(SIMULATION_START, SIMULATION_END)
    cache = HistoricalDataCache(SIMULATION_START, SIMULATION_END)
    init_simulation_cache(cache)
        
    add_trace_processor(LogTracer())
    traders = create_traders()
    
    # Track which traders are bankrupt
    bankrupt_traders = set()
    
    # Loop through each trading day
    day_count = 0
    simulation_start_time = datetime.now()
    
    while not clock.is_complete():
        day_count += 1
        current_date = clock.get_current_date()        
        
        print(f"\n{'='*80}")
        print(f"DAY {day_count}: {current_date}")
        print("="*80)
        
        # Run only non-bankrupt traders
        active_traders = [t for t in traders if t.name not in bankrupt_traders]
        
        if not active_traders:
            print("\nAll traders bankrupt! Ending simulation.")
            break
        
        try:
            await asyncio.gather(*[trader.run() for trader in active_traders])
        except Exception as e:
            print(f"Error in trading cycle: {e}")
            import traceback
            traceback.print_exc()
        
        # Check for bankruptcies after each day
        for trader in traders:
            if trader.name not in bankrupt_traders:
                account = Account.get(trader.name)
                if account.is_bankrupt():
                    bankrupt_traders.add(trader.name)
                    pv = account.calculate_portfolio_value()
                    print(f"\n💀 {trader.name} is BANKRUPT! Portfolio value: ${pv:.2f}")
                    print(f"   {trader.name} will no longer trade.")
        
        clock.advance()
    
    # Calculate simulation speed
    simulation_end_time = datetime.now()
    simulation_duration = (simulation_end_time - simulation_start_time).total_seconds()
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    print(f"Simulated {day_count} trading days in {simulation_duration:.1f} seconds")

    print("="*80)
    print_simulation_results(traders, bankrupt_traders)
    
    # Clear simulation state after completion
    init_simulation_cache(None) 
    clear_simulation_date()

def print_simulation_results(traders: List[Trader], bankrupt_traders: set):
    """Display final simulation results"""
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    results = []
    for trader in traders:
        account = Account.get(trader.name)
        pv = account.calculate_portfolio_value()
        pnl = account.calculate_profit_loss(pv)
        roi = (pnl / INITIAL_BALANCE) * 100
        
        results.append({
            'name': trader.name,
            'pv': pv,
            'pnl': pnl,
            'roi': roi,
            'trades': len(account.transactions),
            'bankrupt': trader.name in bankrupt_traders
        })
    
    # Sort by ROI (best first)
    results.sort(key=lambda x: x['roi'], reverse=True)
    
    for i, result in enumerate(results, 1):
        status = "BANKRUPT" if result['bankrupt'] else "Active"
        
        print(f"\n{i}. {result['name']} [{status}]")
        print(f"   Final Portfolio Value: ${result['pv']:,.2f}")
        print(f"   P&L: ${result['pnl']:,.2f}")
        print(f"   ROI: {result['roi']:.2f}%")
        print(f"   Total Trades: {result['trades']}")
    
    # Summary
    active_count = len([r for r in results if not r['bankrupt']])
    bankrupt_count = len([r for r in results if r['bankrupt']])
    
    print("\n" + "-"*80)
    print(f"Summary: {active_count} survived, {bankrupt_count} went bankrupt")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        if SIMULATION_MODE:
            asyncio.run(run_simulation())
        else:
            print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
            asyncio.run(run_every_n_minutes())
    except KeyboardInterrupt:
        print("TRADING FLOOR STOPPED (Ctrl+C)")
