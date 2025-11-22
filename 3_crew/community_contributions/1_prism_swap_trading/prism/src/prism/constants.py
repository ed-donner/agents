# src/prism/constants.py
"""Constants for PRISM trading system."""

import os

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ============================================================================
# AI/MODEL CONFIGURATION
# ============================================================================

MODEL = "gpt-4o-mini"

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================

# Market data
TENORS = ["2Y", "5Y", "10Y", "30Y"]
DEFAULT_CURRENCY = "USD"
