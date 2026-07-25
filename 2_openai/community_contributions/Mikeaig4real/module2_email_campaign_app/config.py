"""
Config for app
"""

import os
from dotenv import load_dotenv

from debug import debug_print


load_dotenv(override=True)


openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

debug_print("OPENROUTER_KEY set:", bool(openrouter_api_key))