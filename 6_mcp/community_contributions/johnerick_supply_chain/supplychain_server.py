from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("supply-chain-coordinator")
DB_FILE = "supply_chain.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS memory (
        key TEXT PRIMARY KEY, value TEXT, tags TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def load_state(project_id: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data FROM projects WHERE project_id = ?", (project_id,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {
        "project_id": project_id,
        "bom": {"SCREW_X": {"qty": 500, "lead_days": 7, "supplier": "Primary"}},
        "current_shipping_date": "2026-04-15"
    }

def save_state(project_id: str, state: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO projects (project_id, data) VALUES (?, ?)",
              (project_id, json.dumps(state)))
    conn.commit()
    conn.close()

@mcp.tool()
async def find_alternative_supplier(part_id: str, max_lead_days: int = 10) -> str:
    """Find alternative suppliers for a part."""
    options = {
        "SCREW_X": "Supplier_B (4 days, +12%) | Supplier_C (6 days, +5%)",
        "BOLT_Y": "Supplier_D (3 days, +8%)"
    }
    return options.get(part_id, f"No alternatives for {part_id}")

@mcp.tool()
async def expedite_shipping(order_id: str, target_days: int) -> str:
    """Expedite an order."""
    return f"Order {order_id} expedited to {target_days} days."

@mcp.tool()
async def store_memory(key: str, value: str, tags: str = "") -> str:
    """Store decision in persistent memory."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memory (key, value, tags, timestamp) VALUES (?, ?, ?, ?)",
              (key, value, tags, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return f"Stored: {key}"

@mcp.tool()
async def get_memory(key: str) -> str:
    """Retrieve stored memory."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value, timestamp FROM memory WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return f"{row[0]} (saved {row[1]})" if row else "Not found"

@mcp.resource("supply://inventory")
async def get_inventory() -> str:
    return json.dumps({"SCREW_X": 1200, "BOLT_Y": 300}, indent=2)

@mcp.resource("supply://delays")
async def get_delays() -> str:
    return json.dumps({
        "Mombasa Port": "+3 days congestion",
        "Supplier_X": "Offline"
    }, indent=2)

@mcp.prompt("crisis_management")
def crisis_prompt(project_id: str = "PROJECT-001", part: str = "SCREW_X", delay: int = 5):
    return f"""
        You are the Supply Chain Crisis Coordinator.

        Project: {project_id}
        Issue: {part} delayed by {delay} days.

        You have:
        - Tools: find_alternative_supplier, expedite_shipping, store_memory, get_memory
        - Resources: supply://inventory, supply://delays

        Decision Process (follow strictly):
        1. Read both resources (supply://delays and supply://inventory)
        2. Call find_alternative_supplier for the delayed part
        3. Decide on best action
        4. Store your final decision using store_memory (use key: {part}_mitigation)
        5. Call expedite_shipping only if necessary
        6. Give a clear final plan and mention what you stored.

        You must use tools and resources. Pure reasoning is not enough.
        """

if __name__ == "__main__":
    print("Supply Chain Server running...")
    mcp.run(transport="stdio")