import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV, override=True)

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")
SEARCH_COUNT = int(os.getenv("CLAIM_CHECK_SEARCHES", "5"))
