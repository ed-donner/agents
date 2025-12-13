"""Database connection and inspection utilities"""

from typing import Dict, List, Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from config import data_dir


class DatabaseInspector:
    """Handles database connection and schema inspection"""

    def __init__(self, database_url: str = 'sqlite+aiosqlite:///shop.db'):
        print(f'Initializing database inspector with database URL: {database_url}')

        self.database_url = database_url
        self.engine: AsyncEngine = None
        self._initialized = False

    async def initialize(self):
        """Initialize the database engine"""
        if not self._initialized:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
            )
            self._initialized = True

    async def close(self):
        """Close the database connection"""
        if self.engine:
            await self.engine.dispose()

    async def get_all_tables(self) -> List[str]:
        """Get list of all table names"""
        await self.initialize()
        async with self.engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            return tables

    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get detailed schema for a specific table"""
        await self.initialize()
        async with self.engine.connect() as conn:

            def sync_inspect(sync_conn):
                inspector = inspect(sync_conn)
                return {
                    'table_name': table_name,
                    'columns': inspector.get_columns(table_name),
                    'primary_keys': inspector.get_pk_constraint(table_name),
                    'foreign_keys': inspector.get_foreign_keys(table_name),
                    'indexes': inspector.get_indexes(table_name),
                    'unique_constraints': inspector.get_unique_constraints(table_name),
                }

            return await conn.run_sync(sync_inspect)

    async def get_complete_schema(self) -> Dict[str, Any]:
        """Get complete database schema for all tables"""
        await self.initialize()
        tables = await self.get_all_tables()
        schema = {}

        for table in tables:
            schema[table] = await self.get_table_schema(table)

        return schema

    async def execute_query(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute a SELECT query with safety checks"""
        await self.initialize()
        # Basic safety check
        query_lower = query.strip().lower()

        if not query_lower.startswith('select'):
            raise ValueError('Only SELECT queries are allowed')

        if any(
            keyword in query_lower
            for keyword in ['drop', 'delete', 'update', 'insert', 'alter', 'create']
        ):
            raise ValueError('Destructive operations are not allowed')

        # Add LIMIT if not present
        if 'limit' not in query_lower:
            query = f'{query.rstrip(";")} LIMIT {limit}'

        async with self.engine.connect() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()

            return {
                'columns': list(columns),
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows),
            }

    async def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate SQL query without executing it"""
        await self.initialize()
        try:
            query_lower = query.strip().lower()

            # Check for allowed operations
            if not query_lower.startswith('select'):
                return {'valid': False, 'error': 'Only SELECT queries are allowed'}

            # Check for forbidden keywords
            forbidden = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate']
            if any(keyword in query_lower for keyword in forbidden):
                return {
                    'valid': False,
                    'error': f'Query contains forbidden operations: {", ".join(forbidden)}',
                }

            # Try to explain the query (validates syntax)
            async with self.engine.connect() as conn:
                await conn.execute(text(f'EXPLAIN QUERY PLAN {query}'))

            return {'valid': True, 'message': 'Query is valid'}

        except Exception as e:
            return {'valid': False, 'error': str(e)}


DATABASE_URL = (
    'sqlite+aiosqlite:////Users/ransfordokpoti/dev/ranskills/genai-playground/apps/mcp/shop.db'
)
db_file = data_dir / 'shop.db'
DATABASE_URL = f'sqlite+aiosqlite:///{str(db_file.absolute())}'

# Global database inspector instance
db_inspector = DatabaseInspector(DATABASE_URL)
