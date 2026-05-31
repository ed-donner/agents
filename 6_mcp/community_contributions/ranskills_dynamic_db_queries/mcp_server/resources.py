"""MCP Resources for database schema"""

from typing import Dict, Any
import json
from db import db_inspector


async def get_resource(uri: str) -> str:
    """
    Get resource content based on URI

    Supported URIs:
    - db://schema/all - Complete database schema
    - db://schema/tables - List of all tables
    - db://schema/table/{table_name} - Specific table schema
    """

    if uri == 'db://schema/all':
        schema = await db_inspector.get_complete_schema()
        return json.dumps(schema, indent=2, default=str)

    elif uri == 'db://schema/tables':
        tables = await db_inspector.get_all_tables()
        return json.dumps({'tables': tables}, indent=2)

    elif uri.startswith('db://schema/table/'):
        table_name = uri.split('/')[-1]
        schema = await db_inspector.get_table_schema(table_name)
        return json.dumps(schema, indent=2, default=str)

    else:
        raise ValueError(f'Unknown resource URI: {uri}')


def list_resources() -> list:
    """
    List all available resources

    Returns:
        List of resource definitions
    """
    return [
        {
            'uri': 'db://schema/all',
            'name': 'Complete Database Schema',
            'description': 'Full schema for all tables in the database',
            'mimeType': 'application/json',
        },
        {
            'uri': 'db://schema/tables',
            'name': 'Table List',
            'description': 'List of all tables in the database',
            'mimeType': 'application/json',
        },
        {
            'uri': 'db://schema/table/{table_name}',
            'name': 'Table Schema',
            'description': 'Detailed schema for a specific table (replace {table_name})',
            'mimeType': 'application/json',
        },
    ]
