#!/usr/bin/env python
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv

from datetime import datetime

from debate.crew import Debate

# Load environment variables from the .env file in the agents root directory
env_path = Path("/Users/gonenc_aydin/Desktop/The_Complete_AI_Agent_Course/agents/.env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"⚠️  .env file not found at: {env_path}")
    # Fallback to default .env loading
    load_dotenv(override=True)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'motion': 'Llm lerle agi yalan. Bunlar tahmin yarışması oynayan oyuncaklar, bi bok bildikleri yok.',
    }
    
    try:
        result = Debate().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
