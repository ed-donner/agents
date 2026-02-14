# src/prism/database.py
"""Database connection, schema, and seed data for PRISM."""
import os
import sqlite3

# Database Schema
SCHEMA_SQL = """
-- Create positions table
CREATE TABLE IF NOT EXISTS swap_positions (
    position_id TEXT PRIMARY KEY,
    trade_date TEXT NOT NULL,
    maturity_date TEXT NOT NULL,
    notional REAL NOT NULL,
    fixed_rate REAL NOT NULL,
    float_index TEXT NOT NULL,
    pay_receive TEXT NOT NULL,
    currency TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create market rates table
CREATE TABLE IF NOT EXISTS market_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenor TEXT NOT NULL,
    currency TEXT NOT NULL,
    mid_rate REAL NOT NULL,
    bid_rate REAL,
    ask_rate REAL,
    timestamp TEXT NOT NULL,
    source TEXT
);

-- Create trade signals table
CREATE TABLE IF NOT EXISTS trade_signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id TEXT,
    signal_type TEXT,
    reason TEXT,
    current_pnl REAL,
    recommended_action TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    executed INTEGER DEFAULT 0,
    FOREIGN KEY (position_id) REFERENCES swap_positions(position_id)
);
"""


class DatabaseConnection:
    """Manages database connections and query execution."""

    def __init__(self, db_path="prism.db"):
        """Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file (default: "prism.db")
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Use row_factory to get dict-like results (similar to RealDictCursor)
            self.conn.row_factory = sqlite3.Row
            return self.conn
        except Exception:
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=None):
        """Execute a query and return results."""
        cursor = self.conn.cursor()
        try:
            # SQLite uses ? placeholders instead of %s
            # Convert PostgreSQL-style %s to SQLite-style ?
            if params:
                query = query.replace('%s', '?')
            cursor.execute(query, params or [])

            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                # Convert Row objects to dicts for compatibility
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                rowcount = cursor.rowcount
                return rowcount
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def initialize_schema(self):
        """Initialize database schema from SQL string."""
        cursor = self.conn.cursor()
        try:
            cursor.executescript(SCHEMA_SQL)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()


def initialize_database():
    """Initialize the database with schema."""
    # Delete existing database for fresh start
    if os.path.exists("prism.db"):
        os.remove("prism.db")

    db = DatabaseConnection()
    db.connect()
    db.initialize_schema()
    db.close()
    seed_positions()


def seed_positions():
    """Insert sample swap positions for testing."""
    db = DatabaseConnection()
    db.connect()

    # Sample positions
    positions = [
        (
            "SWP001",
            "2024-01-15",
            "2029-01-15",
            10000000,
            4.25,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP002",
            "2024-03-20",
            "2034-03-20",
            25000000,
            4.50,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
        (
            "SWP003",
            "2024-06-10",
            "2029-06-10",
            15000000,
            4.10,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP004",
            "2024-08-05",
            "2027-08-05",
            8000000,
            3.95,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
    ]

    insert_query = """
        INSERT OR IGNORE INTO swap_positions
        (position_id, trade_date, maturity_date, notional, fixed_rate, float_index, pay_receive, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    for position in positions:
        db.execute_query(insert_query, position)

    db.close()
