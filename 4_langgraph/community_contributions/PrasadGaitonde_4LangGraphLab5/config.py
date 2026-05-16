"""
Configuration for the Intelligent Data Analysis Agent.
Database connection strings, schema definitions, and agent settings.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/analysis.db")
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "./data/agent_memory.db")

# Sample database schema for demonstration (SQLite)
SAMPLE_SCHEMA = """
-- Example: Sales database schema
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    email TEXT,
    region TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock_quantity INTEGER
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL,
    status TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

# Agent Configuration
MAX_QUERY_REWRITE_ATTEMPTS = int(os.getenv("MAX_QUERY_REWRITE_ATTEMPTS", "3"))
CLARIFYING_QUESTION_COUNT = int(os.getenv("CLARIFYING_QUESTION_COUNT", "3"))

# LLM Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", DEFAULT_MODEL)
QUERY_WRITER_MODEL = os.getenv("QUERY_WRITER_MODEL", DEFAULT_MODEL)
QUERY_CHECKER_MODEL = os.getenv("QUERY_CHECKER_MODEL", DEFAULT_MODEL)
CLARIFIER_MODEL = os.getenv("CLARIFIER_MODEL", DEFAULT_MODEL)

# Tool Configuration
ALLOW_DANGEROUS_QUERIES = os.getenv("ALLOW_DANGEROUS_QUERIES", "false").lower() == "true"
QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS", "30"))
MAX_ROWS_RETURNED = int(os.getenv("MAX_ROWS_RETURNED", "100"))
