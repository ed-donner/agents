#!/usr/bin/env python3
"""
ETF Portfolio Analyzer - Main Entry Point
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.ui.dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()
