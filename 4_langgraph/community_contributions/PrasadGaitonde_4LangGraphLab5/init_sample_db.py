"""
Initialize the sample database with demo data.
Run this script to create a sample sales database for testing.
"""
import sqlite3
from pathlib import Path
from config import DATABASE_PATH


def create_sample_database():
    """Create sample database with demo data."""
    # Ensure directory exists
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database if present
    if Path(DATABASE_PATH).exists():
        Path(DATABASE_PATH).unlink()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT,
            region TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock_quantity INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL,
            status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Insert sample customers
    customers = [
        (1, "Acme Corporation", "contact@acme.com", "North"),
        (2, "TechStart Inc", "info@techstart.io", "South"),
        (3, "Global Retail Ltd", "sales@globalretail.com", "East"),
        (4, "Local Shop LLC", "owner@localshop.com", "West"),
        (5, "Enterprise Co", "procurement@enterprise.co", "North"),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", customers)

    # Insert sample products
    products = [
        (1, "Widget A", "Electronics", 29.99, 100),
        (2, "Widget B", "Electronics", 49.99, 75),
        (3, "Gadget Pro", "Electronics", 199.99, 25),
        (4, "Office Chair", "Furniture", 149.99, 50),
        (5, "Desk Lamp", "Furniture", 39.99, 200),
        (6, "Notebook Set", "Office Supplies", 12.99, 500),
        (7, "Pen Pack", "Office Supplies", 8.99, 1000),
        (8, "Monitor Stand", "Furniture", 79.99, 30),
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

    # Insert sample orders
    orders = [
        (1, 1, "2025-01-15 10:30:00", 299.90, "completed"),
        (2, 2, "2025-01-18 14:45:00", 549.95, "completed"),
        (3, 3, "2025-02-01 09:15:00", 1299.88, "completed"),
        (4, 1, "2025-02-10 16:20:00", 89.97, "completed"),
        (5, 4, "2025-02-15 11:00:00", 459.96, "pending"),
        (6, 5, "2025-03-01 08:30:00", 2499.75, "completed"),
        (7, 2, "2025-03-05 13:45:00", 179.97, "shipped"),
        (8, 3, "2025-03-10 15:30:00", 899.91, "pending"),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    # Insert sample order items
    order_items = [
        (1, 1, 1, 5, 29.99),
        (2, 1, 3, 1, 199.99),
        (3, 1, 6, 4, 12.99),
        (4, 2, 2, 3, 49.99),
        (5, 2, 4, 2, 149.99),
        (6, 2, 7, 5, 8.99),
        (7, 3, 3, 5, 199.99),
        (8, 3, 4, 2, 149.99),
        (9, 4, 5, 2, 39.99),
        (10, 4, 6, 1, 12.99),
        (11, 5, 1, 4, 29.99),
        (12, 5, 8, 3, 79.99),
        (13, 6, 3, 10, 199.99),
        (14, 6, 4, 5, 149.99),
        (15, 7, 5, 3, 39.99),
        (16, 7, 6, 5, 12.99),
        (17, 8, 2, 6, 49.99),
        (18, 8, 8, 5, 79.99),
    ]
    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", order_items)

    conn.commit()
    conn.close()

    print(f"Sample database created at: {DATABASE_PATH}")
    print("Tables created: customers, products, orders, order_items")
    print("Sample data inserted:")
    print(f"  - {len(customers)} customers")
    print(f"  - {len(products)} products")
    print(f"  - {len(orders)} orders")
    print(f"  - {len(order_items)} order items")


if __name__ == "__main__":
    create_sample_database()
