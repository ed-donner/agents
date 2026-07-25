import sys
import json
import os
from pathlib import Path

# Insert project root so we can resolve mcp standard libraries if needed
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ExamStudyServer")

DB_FILE = Path(__file__).parent / "study_db.json"

def load_db():
    if not DB_FILE.exists():
        return {"materials": {}, "flashcards": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

@mcp.tool()
def add_study_material(topic: str, content: str) -> str:
    """Save raw study material or notes for a given topic."""
    db = load_db()
    db["materials"][topic] = content
    save_db(db)
    return f"Material for topic '{topic}' saved successfully."

@mcp.tool()
def get_study_material(topic: str) -> str:
    """Retrieve saved study material or notes for a given topic."""
    db = load_db()
    return db["materials"].get(topic, f"No material found for topic '{topic}'.")

@mcp.tool()
def list_topics() -> str:
    """Return a list of all current study topics available."""
    db = load_db()
    topics = list(db["materials"].keys()) + list(db["flashcards"].keys())
    topics = list(set(topics))
    return f"Available topics: {', '.join(topics) if topics else 'None'}"

@mcp.tool()
def save_flashcards(topic: str, questions_and_answers: str) -> str:
    """Save generated flashcards as a string (Q&A pairs) to persist for future revision."""
    db = load_db()
    db["flashcards"][topic] = questions_and_answers
    save_db(db)
    return f"Flashcards for topic '{topic}' saved successfully."

@mcp.tool()
def get_flashcards(topic: str) -> str:
    """Retrieve previously generated flashcards for a specific topic."""
    db = load_db()
    return db["flashcards"].get(topic, f"No flashcards found for topic '{topic}'.")

if __name__ == "__main__":
    mcp.run()
