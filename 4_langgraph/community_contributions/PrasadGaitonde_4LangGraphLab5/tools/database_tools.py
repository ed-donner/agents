"""
Database tools for the Intelligent Data Analysis Agent.
Provides database connection, schema inspection, SQL validation, and query execution.
"""
import sqlite3
import asyncio
from typing import Optional, Tuple, List, Any, Dict
from langchain_core.tools import tool
from config import DATABASE_PATH, MAX_ROWS_RETURNED, QUERY_TIMEOUT_SECONDS, SAMPLE_SCHEMA
import pandas as pd


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database with sample schema if it doesn't exist."""
        import os
        from pathlib import Path

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create database with sample tables if new
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(SAMPLE_SCHEMA)
            conn.commit()
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve database schema information."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [
                {"name": row[1], "type": row[2], "not_null": bool(row[3]), "pk": bool(row[5])}
                for row in cursor.fetchall()
            ]

            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = [
                {"from": row[3], "to": row[2], "table": row[2]}
                for row in cursor.fetchall()
            ]

            schema[table] = {
                "columns": columns,
                "foreign_keys": foreign_keys
            }

        conn.close()
        return schema

    def execute_query(self, sql: str, params: tuple = ()) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Execute a SQL query safely.
        Returns: (results as list of dicts, error message or None)
        """
        # Security: Only allow SELECT queries
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return None, "Only SELECT queries are allowed for safety"

        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE", "CREATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper and keyword not in ["SELECT"]:
                # Allow CREATE/DROP in subqueries for legitimate purposes
                if sql_upper.startswith(keyword):
                    return None, f"Query contains potentially dangerous operation: {keyword}"

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            # Convert to list of dicts
            results = [dict(row) for row in rows[:MAX_ROWS_RETURNED]]
            return results, None
        except sqlite3.Error as e:
            return None, str(e)
        finally:
            conn.close()

    def validate_query(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query syntax without executing.
        Returns: (is_valid, error_message)
        """
        conn = self.get_connection()
        try:
            # Use EXPLAIN to check syntax
            conn.execute(f"EXPLAIN {sql}")
            return True, "Query syntax is valid"
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def get_table_sample(self, table_name: str, limit: int = 5) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Get a sample of rows from a table for exploration."""
        # Validate table name to prevent SQL injection
        schema = self.get_schema()
        if table_name not in schema:
            return None, f"Table '{table_name}' not found in database"

        return self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")


# Create LangChain tools from DatabaseManager methods
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get or create the database manager singleton."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@tool
def inspect_database_schema() -> str:
    """
    Inspect the database schema to see available tables and their columns.
    Use this tool before writing queries to understand the data structure.
    Returns a formatted description of all tables, columns, and relationships.
    """
    db = get_db_manager()
    schema = db.get_schema()

    result = ["Database Schema:"]
    for table_name, info in schema.items():
        result.append(f"\n## Table: {table_name}")
        result.append("Columns:")
        for col in info["columns"]:
            pk = " (PRIMARY KEY)" if col["pk"] else ""
            nn = " NOT NULL" if col["not_null"] else ""
            result.append(f"  - {col['name']}: {col['type']}{pk}{nn}")

        if info["foreign_keys"]:
            result.append("Foreign Keys:")
            for fk in info["foreign_keys"]:
                result.append(f"  - {fk['from']} -> {fk['table']}.{fk['to']}")

    return "\n".join(result)


@tool
def execute_sql_query(sql_query: str) -> str:
    """
    Execute a SQL SELECT query against the database.
    Use this tool to retrieve data based on your analysis needs.

    Args:
        sql_query: A valid SQL SELECT query

    Returns:
        Query results as a formatted string, or an error message if the query failed
    """
    db = get_db_manager()
    results, error = db.execute_query(sql_query)

    if error:
        return f"Query Error: {error}"

    if not results:
        return "Query executed successfully but returned no results."

    # Format as table-like string
    df = pd.DataFrame(results)
    return df.to_string(index=False)


@tool
def validate_sql_syntax(sql_query: str) -> str:
    """
    Validate SQL query syntax without executing it.
    Use this tool to check your query before running it.

    Args:
        sql_query: The SQL query to validate

    Returns:
        Validation result message
    """
    db = get_db_manager()
    is_valid, message = db.validate_query(sql_query)
    return f"{'Valid' if is_valid else 'Invalid'}: {message}"


@tool
def get_table_sample_data(table_name: str) -> str:
    """
    Get a sample of rows from a specific table to understand its data.
    Use this tool when exploring a new table or verifying data format.

    Args:
        table_name: Name of the table to sample

    Returns:
        Sample rows as a formatted string, or an error message
    """
    db = get_db_manager()
    results, error = db.get_table_sample(table_name)

    if error:
        return f"Error: {error}"

    if not results:
        return f"Table '{table_name}' exists but contains no data."

    df = pd.DataFrame(results)
    return f"Sample from '{table_name}':\n" + df.to_string(index=False)


@tool
def explain_query_plan(sql_query: str) -> str:
    """
    Get the SQLite query execution plan to understand query performance.
    Use this tool to identify slow queries or understand join strategies.

    Args:
        sql_query: The SQL query to analyze

    Returns:
        Query execution plan as a formatted string
    """
    db = get_db_manager()
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {sql_query}")
        plan_rows = cursor.fetchall()

        result = ["Query Execution Plan:"]
        for row in plan_rows:
            result.append(f"  {row[3]}")  # The plan detail is in column 3

        return "\n".join(result)
    except sqlite3.Error as e:
        return f"Error getting query plan: {e}"
    finally:
        conn.close()


async def database_tools() -> List:
    """Initialize and return database tools."""
    # Initialize the database
    get_db_manager()

    return [
        inspect_database_schema,
        execute_sql_query,
        validate_sql_syntax,
        get_table_sample_data,
        explain_query_plan
    ]
