import sys
import os
import asyncio
import threading

sys.path.insert(0, os.path.dirname(__file__))

from src.ui.app import create_ui
from trading_floor import run_every_n_minutes, RUN_EVERY_N_MINUTES

def run_trading_floor_in_background():
    """Run trading floor in background thread"""
    asyncio.run(run_every_n_minutes())

if __name__ == "__main__":
    print("="*60)
    print("AUTONOMOUS TRADING FLOOR - STARTING")
    print("="*60)
    print(f"Trading cycle: Every {RUN_EVERY_N_MINUTES} minutes")
    print("Agents: 4 Traders + Risk Manager + News Sentinel")
    print("UI: Gradio dashboard with real-time monitoring")
    print("="*60)

    # Start trading floor in background thread
    trading_thread = threading.Thread(target=run_trading_floor_in_background, daemon=True)
    trading_thread.start()
    print("✓ Trading floor started in background")

    # Launch UI in main thread
    print("✓ Launching UI dashboard...")
    ui = create_ui()
    ui.launch(inbrowser=True)
