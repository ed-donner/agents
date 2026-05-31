import os
import sqlite3
import asyncio
from dotenv import load_dotenv
from agents import Agent, function_tool, Runner

load_dotenv(override=True)

@function_tool
def create_database() -> str:
    print("Creating database...")

    # --- Ensure db folder exists ---
    DB_FOLDER = "db"
    os.makedirs(DB_FOLDER, exist_ok=True)

    # --- Define the database path ---
    DB_PATH = os.path.join(DB_FOLDER, "inventory.db")

    # --- Connect to the database ---
    # If the file doesn’t exist, sqlite3 will create it automatically
    conn = sqlite3.connect(DB_PATH)
    conn.close()

    return { "status": "success", "message": f"Database created at: {DB_PATH}" }

@function_tool
def create_products_table(db_path: str = "db/inventory.db") -> str:
    print("Creating the products table")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name VARCHAR(255),
            purchase_price REAL,
            selling_price REAL,
            quantity_on_hand INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return { "status": "success", "message": "Created 'products' table" }

@function_tool
def add_test_products_table_data(db_path: str = "db/inventory.db") -> str:
    print("Adding test data to products table")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products values(1, 'computer', 2000.00, 2500.00, 10)")
    cursor.execute("INSERT INTO products values(2, 'monitor', 150.00, 175.00, 15)")
    cursor.execute("INSERT INTO products values(3, 'mouse', 35.00, 40.00, 18)")
    cursor.execute("INSERT INTO products values(4, 'laptop', 1800.00, 2200.00, 30)")

    conn.commit()
    conn.close()

    return { "status": "success", "message": "Added test data to the 'products' table" }

@function_tool
def delete_all_rows_products_table(db_path: str = "db/inventory.db") -> str:
    print("Deleting all rows from products table")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")

    conn.commit()
    conn.close()

    return { "status": "success", "message": "Deleted all rows from the 'products' table" }

@function_tool
def sell_products(product: str, quantity: int, db_path: str = "db/inventory.db") -> str:
    print("Reduce the quantity of a product in the products table")

    if product is None or quantity is None:
        return { "status": "error", "message": f"product or quantity parameters were not found" }

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT quantity_on_hand FROM products WHERE name=?", product)
    row = cursor.fetchone()

    if row is None:
        return { "status": "error", "message": f"{product} not found in the 'products' table" }

    current_quantity = row[0]
    new_quantity = current_quantity - quantity

    if new_quantity < 0:
        return { "status": "error", "message": f"Cannot sell {quantity} of {product}, current quantity is {current_quantity}" }

    cursor.execute("UPDATE products SET quantity_on_hand=? WHERE name=?", (new_quantity, product))

    conn.commit()
    conn.close()

    return { "status": "success", "message": f"Sold {quantity} of {product} and reduced quantity in the products table" }

class DatabaseManagerAgent:
    def __init__(self):
        self.agent = Agent(
            name="Database Manager",
            instructions=(
                "You are a database admin agent."
                "You are given tools to perform the following database admin tasks:"
                "- create the database"
                "- create the products table"
                "- insert data into the products table"
                "- delete all rows from the products table"
                "- sell products, reducing the quantity of a product in the products table"
                "When asked to sell products, use the sell_products tool"
                "No additional output, the tools will print their own output."
                "Only make changes when asked explicitly."
            ),
            tools=[create_database, create_products_table, add_test_products_table_data, delete_all_rows_products_table, sell_products]
        )

    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
