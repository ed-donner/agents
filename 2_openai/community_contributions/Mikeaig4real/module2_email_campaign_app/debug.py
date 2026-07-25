"""
Custom debugger
"""

import os

def debug_print(*args, **kwargs):
    """Print to console only if DEV_ENV is set to 'development'."""
    if os.environ.get("DEV_ENV", "").lower() == "development":
        print(*args, **kwargs)
