from fastmcp import FastMCP
import os
import aiosqlite
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        await c.commit()
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
async def edit_expense(expense_id, date=None, amount=None, category=None, subcategory=None, note=None):
    '''Edit an existing expense entry. Only provided fields will be updated.'''
    async with aiosqlite.connect(DB_PATH) as c:
        # First check if expense exists
        cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
        if not await cur.fetchone():
            return {"status": "error", "message": f"Expense {expense_id} not found"}
        
        # Build dynamic update query
        updates = []
        params = []
        
        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if subcategory is not None:
            updates.append("subcategory = ?")
            params.append(subcategory)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        
        if not updates:
            return {"status": "error", "message": "No fields provided to update"}
        
        params.append(expense_id)
        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
        await c.execute(query, params)
        await c.commit()
        return {"status": "ok", "id": expense_id, "updated_fields": len(updates)}

@mcp.tool()
async def delete_expense(expense_id):
    '''Delete an expense entry by ID.'''
    async with aiosqlite.connect(DB_PATH) as c:
        # Check if expense exists
        cur = await c.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
        if not await cur.fetchone():
            return {"status": "error", "message": f"Expense {expense_id} not found"}
        
        await c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        await c.commit()
        return {"status": "ok", "id": expense_id, "message": "Expense deleted"}
    
@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    async with aiosqlite.connect(DB_PATH) as c:
        cur = await c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        rows = await cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    async with aiosqlite.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = await c.execute(query, params)
        cols = [d[0] for d in cur.description]
        rows = await cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]

@mcp.resource("expense://categories", mime_type="application/json")
async def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()