import os
from pathlib import Path
from dotenv import load_dotenv


def get_config() -> dict:
    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    load_dotenv(env_path, override=True)
    
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "pushover_user": os.getenv("PUSHOVER_USER"),
        "pushover_token": os.getenv("PUSHOVER_TOKEN"),
        "name": "Umar Javed",
        "rag_enabled": True,
        "rag_method": "hybrid_rerank",
        "top_k": 5,
        "query_expansion": True,
        "chunk_size": 500,
        "chunk_overlap": 50
    }
    
    if not config["openai_api_key"]:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    if not config["pushover_user"] or not config["pushover_token"]:
        print("[WARNING] Pushover credentials not found. Notifications will be disabled.")
    
    return config

