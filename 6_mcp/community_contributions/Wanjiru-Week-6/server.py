import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NotesServer")

DB_FILE = Path("notes_db.json")

def load_db():
    if not DB_FILE.exists():
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

@mcp.tool()
def save_note(topic: str, content: str) -> str:
    """Save a note under a topic"""
    db = load_db()
    db[topic] = content
    save_db(db)
    return f"Saved note for {topic}"

@mcp.tool()
def get_note(topic: str) -> str:
    """Retrieve a note by topic"""
    db = load_db()
    return db.get(topic, "No note found")

if __name__ == "__main__":
    mcp.run()
    