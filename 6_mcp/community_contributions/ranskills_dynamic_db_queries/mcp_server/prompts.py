"""MCP Prompt templates"""

import json
from typing import Dict, Any

from db import db_inspector


def get_prompts() -> list:
    """
    Get list of available prompt templates

    Returns:
        List of prompt definitions
    """
    return [
        {
            'name': 'analyze_table',
            'description': 'Analyze a specific table and provide insights',
            'arguments': [
                {
                    'name': 'table_name',
                    'description': 'Name of the table to analyze',
                    'required': True,
                }
            ],
        },
        {
            'name': 'generate_query',
            'description': 'Generate a SQL query based on natural language description',
            'arguments': [
                {
                    'name': 'description',
                    'description': 'Natural language description of what you want to query',
                    'required': True,
                },
                {
                    'name': 'tables',
                    'description': 'Comma-separated list of tables to include',
                    'required': False,
                },
            ],
        },
        {
            'name': 'find_relationships',
            'description': 'Find and explain relationships between tables',
            'arguments': [
                {'name': 'table1', 'description': 'First table name', 'required': True},
                {
                    'name': 'table2',
                    'description': 'Second table name (optional)',
                    'required': False,
                },
            ],
        },
    ]


async def get_prompt(name: str, arguments: Dict[str, Any]) -> str:
    """
    Get a prompt template filled with arguments

    Args:
        name: Name of the prompt
        arguments: Arguments to fill the prompt

    Returns:
        Filled prompt template
    """

    if name == 'analyze_table':
        table_name = arguments.get('table_name')
        schema = await db_inspector.get_table_schema(table_name)

        return f"""Analyze the following table and provide insights:

Table: {table_name}

Schema:
{json.dumps(schema, indent=2, default=str)}

Please provide:
1. A summary of what this table represents
2. Key columns and their purposes
3. Relationships with other tables
4. Potential data quality considerations
5. Suggested queries for common use cases
"""

    elif name == 'generate_query':
        description = arguments.get('description')
        tables = arguments.get('tables', '')

        all_tables = await db_inspector.get_all_tables()
        relevant_schemas = {}

        if tables:
            table_list = [t.strip() for t in tables.split(',')]
            for table in table_list:
                if table in all_tables:
                    relevant_schemas[table] = await db_inspector.get_table_schema(table)
        else:
            for table in all_tables:
                relevant_schemas[table] = await db_inspector.get_table_schema(table)

        return f"""Generate a SQL query for the following request:

Request: {description}

Available tables and schemas:
{json.dumps(relevant_schemas, indent=2, default=str)}

Please provide:
1. A valid SELECT query that fulfills the request
2. Explanation of the query logic
3. Any assumptions made
4. Sample output structure
"""

    elif name == 'find_relationships':
        table1 = arguments.get('table1')
        table2 = arguments.get('table2')

        schema1 = await db_inspector.get_table_schema(table1)

        prompt = f"""Analyze relationships for table: {table1}

Table Schema:
{json.dumps(schema1, indent=2, default=str)}

"""

        if table2:
            schema2 = await db_inspector.get_table_schema(table2)
            prompt += f"""
Compare with table: {table2}

Table Schema:
{json.dumps(schema2, indent=2, default=str)}

Please identify:
1. Direct foreign key relationships between these tables
2. Indirect relationships through other tables
3. Suggested JOIN patterns
"""
        else:
            prompt += """
Please identify:
1. All foreign key relationships from this table
2. All foreign key relationships to this table
3. Common query patterns involving related tables
"""

        return prompt

    else:
        raise ValueError(f'Unknown prompt: {name}')
