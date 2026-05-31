"""MCP Tools for database operations"""

from typing import Dict, Any
from db import db_inspector


async def query_database(sql: str, limit: int = 100) -> Dict[str, Any]:
    """
    Execute a SELECT query on the database

    Args:
        sql: SQL SELECT query to execute
        limit: Maximum number of rows to return (default: 100)

    Returns:
        Query results with columns and rows
    """
    try:
        result = await db_inspector.execute_query(sql, limit)
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def describe_table(table_name: str) -> Dict[str, Any]:
    """
    Get detailed schema information for a specific table

    Args:
        table_name: Name of the table to describe

    Returns:
        Table schema including columns, keys, and constraints
    """
    try:
        schema = await db_inspector.get_table_schema(table_name)
        return {'success': True, 'schema': schema}
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def list_tables() -> Dict[str, Any]:
    """
    Get a list of all tables in the database

    Returns:
        List of table names
    """
    try:
        tables = await db_inspector.get_all_tables()
        return {'success': True, 'tables': tables}
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def validate_sql(sql: str) -> Dict[str, Any]:
    """
    Validate SQL query without executing it

    Args:
        sql: SQL query to validate

    Returns:
        Validation result
    """
    try:
        result = await db_inspector.validate_query(sql)
        return {'success': True, 'validation': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}
