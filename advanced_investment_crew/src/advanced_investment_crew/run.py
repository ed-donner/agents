#!/usr/bin/env python3
"""
ETF Portfolio Analyzer - Main Entry Point

Run this file to start the Streamlit dashboard:
    streamlit run run.py
    
Or:
    python run.py
"""

import sys
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point"""
    try:
        # Import and run dashboard
        from src.ui.dashboard import run_dashboard
        run_dashboard()
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if running with streamlit
    if "streamlit" not in sys.argv[0]:
        print("Starting Streamlit dashboard...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", __file__,
            "--server.headless", "true"
        ])
    else:
        main()
