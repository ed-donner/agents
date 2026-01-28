"""Main MCP Server"""

import logging

from mcp.server.fastmcp import FastMCP

import tools
import resources
import prompts
from db import db_inspector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='mcp_server.log',
    filemode='a',
)

# Create MCP server instance
mcp = FastMCP(name='database-inspector')


# Register tools
@mcp.tool()
async def query_database(sql: str, limit: int = 100):
    """Execute a SELECT query on the database"""
    return await tools.query_database(sql, limit)


@mcp.tool()
async def describe_table(table_name: str):
    """Get detailed schema information for a specific table"""
    return await tools.describe_table(table_name)


@mcp.tool()
async def list_tables():
    """Get a list of all tables in the database"""
    return await tools.list_tables()


@mcp.tool()
async def validate_sql(sql: str):
    """Validate SQL query without executing it"""
    return await tools.validate_sql(sql)


# Register resources
@mcp.resource('db://schema/all')
async def complete_schema():
    """Complete database schema for all tables"""
    return await resources.get_resource('db://schema/all')


@mcp.resource('db://schema/tables')
async def table_list():
    """List of all tables"""
    return await resources.get_resource('db://schema/tables')


@mcp.resource('db://schema/table/{table_name}')
async def table_schema(table_name: str):
    """Schema for a specific table"""
    return await resources.get_resource(f'db://schema/table/{table_name}')


# Register prompts
@mcp.prompt()
async def analyze_table(table_name: str):
    """Analyze a specific table and provide insights"""
    return await prompts.get_prompt('analyze_table', {'table_name': table_name})


@mcp.prompt()
async def generate_query(description: str, tables: str = ''):
    """Generate a SQL query based on natural language description"""
    return await prompts.get_prompt(
        'generate_query', {'description': description, 'tables': tables}
    )


@mcp.prompt()
async def find_relationships(table1: str, table2: str = ''):
    """Find and explain relationships between tables"""
    return await prompts.get_prompt('find_relationships', {'table1': table1, 'table2': table2})


async def main():
    """Initialize and run the server"""
    # Initialize database connection
    await db_inspector.initialize()

    try:
        # Run the MCP server
        await mcp.run(transport='stdio')
    finally:
        # Clean up database connection
        await db_inspector.close()


if __name__ == '__main__':
    logging.info('Starting MCP server')
    mcp.run(transport='stdio')
