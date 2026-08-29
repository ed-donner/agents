"""
Configuration and environment setup for the chatbot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configuration
MODEL_NAME = "claude-3-7-sonnet-latest"
MAX_TOKENS = 1000
RATE_LIMIT = 10  # messages per minute
DEFAULT_NAME = "Taissa Conde"

# Pushover configuration
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")