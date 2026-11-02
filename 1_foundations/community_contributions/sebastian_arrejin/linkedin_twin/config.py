import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "twin.db"
EMBEDDINGS_CACHE = DATA_DIR / "embeddings.json"

MODEL = os.getenv("TWIN_MODEL", "gpt-5.4-mini")
EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "gpt-5.4-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Number of extra attempts the twin gets after the evaluator rejects an answer
MAX_EVALUATION_RETRIES = 2

# The database tab exposes visitor emails, so it must stay off on a public deployment
SHOW_ADMIN_TAB = os.getenv("SHOW_ADMIN_TAB", "false").lower() == "true"

NAME = "Sebastian Arrejin"
LINKEDIN_URL = "https://www.linkedin.com/in/sebastian-arrejin-047981146/"

IDENTITY = f"""
- Name: {NAME} (full name as shown on his ISTQB certificate: Carlos Sebastian Cayetano Arrejin)
- Profession: QA Engineer, experienced in manual and automation testing
- Current company: CFOTech IT Global Services
- Location: Matheu, Buenos Aires Province, Argentina
- LinkedIn: {LINKEDIN_URL}
""".strip()
