"""
Simple SQLite-backed data access for inventory, shipments, and forecast.
"""
import sqlite3

DB = "timothy_supplychain.db"

def get_inventory():
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (Product TEXT, Stock INTEGER, Location TEXT)''')
            rows = cursor.execute('SELECT Product, Stock, Location FROM inventory').fetchall()
            if not rows:
                # Seed with demo data if empty
                demo = [("Widget A", 120, "Warehouse 1"), ("Widget B", 80, "Warehouse 2")]
                cursor.executemany('INSERT INTO inventory VALUES (?, ?, ?)', demo)
                conn.commit()
                rows = demo
            return [{"Product": r[0], "Stock": r[1], "Location": r[2]} for r in rows]
    except Exception as e:
        return [{"Product": "Error", "Stock": 0, "Location": str(e)}]

def get_shipments():
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS shipments (ShipmentID INTEGER, Product TEXT, Status TEXT)''')
            rows = cursor.execute('SELECT ShipmentID, Product, Status FROM shipments').fetchall()
            if not rows:
                demo = [(1, "Widget A", "In Transit"), (2, "Widget B", "Delivered")]
                cursor.executemany('INSERT INTO shipments VALUES (?, ?, ?)', demo)
                conn.commit()
                rows = demo
            return [{"ShipmentID": r[0], "Product": r[1], "Status": r[2]} for r in rows]
    except Exception as e:
        return [{"ShipmentID": 0, "Product": "Error", "Status": str(e)}]

def get_forecast():
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS forecast (Product TEXT, Forecast INTEGER)''')
            rows = cursor.execute('SELECT Product, Forecast FROM forecast').fetchall()
            if not rows:
                demo = [("Widget A", 150), ("Widget B", 90)]
                cursor.executemany('INSERT INTO forecast VALUES (?, ?)', demo)
                conn.commit()
                rows = demo
            return [{"Product": r[0], "Forecast": r[1]} for r in rows]
    except Exception as e:
        return [{"Product": "Error", "Forecast": str(e)}]
