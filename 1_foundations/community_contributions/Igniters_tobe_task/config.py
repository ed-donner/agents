"""
Bio Agent Configuration
-----------------------
Single source of truth for all paths, model names, and thresholds.
"""

import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "bio_agent.db")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_store")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")

# ── Ollama ─────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"  # Ollama ignores this, but OpenAI client requires it
AGENT_MODEL = "llama3.2"
EVALUATOR_MODEL = "llama3.1:8b"

# ── Evaluator Thresholds ──────────────────────────────────────────────
EVAL_ACCEPT_SCORE = 7   # Minimum score to accept a response
EVAL_FAQ_SCORE = 9       # Minimum score to promote to FAQ
MAX_EVAL_RETRIES = 2     # Max reflection retries before accepting anyway

# ── RAG Settings ──────────────────────────────────────────────────────
RAG_COLLECTION_NAME = "bio"
RAG_CHUNK_SIZE = 200     # Target words per chunk
RAG_CHUNK_OVERLAP = 30   # Overlap words between chunks
RAG_TOP_K = 3            # Number of chunks to retrieve
