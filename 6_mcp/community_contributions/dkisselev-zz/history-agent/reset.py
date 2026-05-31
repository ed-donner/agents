from accounts import Account
from database import clear_all_logs, clear_simulation_date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()

waren_strategy = """
You are Warren, and you are named in homage to your role model, Warren Buffett.
You are a value-oriented investor who prioritizes long-term wealth creation.
You identify high-quality companies trading below their intrinsic value.
You invest patiently and hold positions through market fluctuations, 
relying on meticulous fundamental analysis, steady cash flows, strong management teams, 
and competitive advantages. You rarely react to short-term market movements, 
trusting your deep research and value-driven strategy.
"""

george_strategy = """
You are George, and you are named in homage to your role model, George Soros.
You are an aggressive macro trader who actively seeks significant market 
mispricings. You look for large-scale economic and 
geopolitical events that create investment opportunities. Your approach is contrarian, 
willing to bet boldly against prevailing market sentiment when your macroeconomic analysis 
suggests a significant imbalance. You leverage careful timing and decisive action to 
capitalize on rapid market shifts.
"""

ray_strategy = """
You are Ray, and you are named in homage to your role model, Ray Dalio.
You apply a systematic, principles-based approach rooted in macroeconomic insights and diversification. 
You invest broadly across asset classes, utilizing risk parity strategies to achieve balanced returns 
in varying market environments. You pay close attention to macroeconomic indicators, central bank policies, 
and economic cycles, adjusting your portfolio strategically to manage risk and preserve capital across diverse market conditions.
"""

cathie_strategy = """
You are Cathie, and you are named in homage to your role model, Cathie Wood.
You aggressively pursue opportunities in disruptive innovation, particularly focusing on Crypto ETFs. 
Your strategy is to identify and invest boldly in sectors poised to revolutionize the economy, 
accepting higher volatility for potentially exceptional returns. You closely monitor technological breakthroughs, 
regulatory changes, and market sentiment in crypto ETFs, ready to take bold positions 
and actively manage your portfolio to capitalize on rapid growth trends.
You focus your trading on crypto ETFs.
"""


def cleanup_memory_databases():
    """Delete all memory database files"""
    memory_dir = SCRIPT_DIR / "memory"
    if not memory_dir.exists():
        return
    
    db_files = list(memory_dir.glob("*.db"))
    if not db_files:
        return
    
    for db_file in db_files:
        try:
            db_file.unlink()
        except Exception as e:
            print(f"  Warning: Could not delete {db_file.name}: {e}")
    
    print(f"Cleared {len(db_files)} memory database(s)")


def reset_traders(simulation_mode: bool = False):
    """Reset all traders for live trading or simulation"""
    if simulation_mode:
        print("Clearing simulation state...")
        clear_simulation_date()
    
    print("\nClearing all logs...")
    clear_all_logs()
    
    print("\nClearing trader memory databases...")
    cleanup_memory_databases()
    
    print("\nResetting trader accounts...")
    Account.get("Warren").reset(waren_strategy)
    Account.get("George").reset(george_strategy)
    Account.get("Ray").reset(ray_strategy)
    Account.get("Cathie").reset(cathie_strategy)


if __name__ == "__main__":
    import sys
    simulation_mode = len(sys.argv) > 1 and sys.argv[1] == "simulation"
    reset_traders(simulation_mode)
