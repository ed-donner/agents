"""Configuration and constants for the Interview Prep Agent"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# LLM Configuration
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.7

# Tavily Configuration
TAVILY_MAX_RESULTS = 3
TAVILY_SEARCH_DEPTH = "advanced"  # "basic" or "advanced"
TAVILY_TIMEOUT = 10

# YouTube Configuration
YOUTUBE_MAX_RESULTS = 3
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_TIMEOUT = 10

# Refinement Settings
MAX_REFINEMENTS = 3

# UI Configuration
UI_TITLE = "Interview Prep Agent with YouTube Search"
UI_SUBTITLE = "*Ask for YouTube videos at any time during refinement!*"
UI_HEIGHT = 500
UI_PLACEHOLDER = "Say 'hi' to start..."

