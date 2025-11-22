# src/prism/database/connection.py
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

from ..utils import logger

load_dotenv()


class DatabaseConnection:
    """Manages database connections and query execution."""

    def __init__(self):
        """Initialize database connection manager."""
        self.database_url = os.getenv("DATABASE_URL")
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            logger.debug("Establishing database connection...")
            self.conn = psycopg2.connect(
                self.database_url, cursor_factory=RealDictCursor
            )
            logger.debug("✅ Database connection established")
            return self.conn
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            logger.debug("Closing database connection...")
            self.conn.close()
            logger.debug("Database connection closed")

    def execute_query(self, query, params=None):
        """Execute a query and return results."""
        cursor = self.conn.cursor()
        try:
            query_type = (
                query.strip().upper().split()[0] if query.strip() else "UNKNOWN"
            )
            logger.debug(f"Executing {query_type} query...")

            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                logger.debug(f"Query returned {len(results)} rows")
                return results
            else:
                self.conn.commit()
                rowcount = cursor.rowcount
                logger.debug(f"Query affected {rowcount} rows")
                return rowcount
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Query execution error: {e}")
            raise
        finally:
            cursor.close()

    def initialize_schema(self, schema_file):
        """Initialize database schema from SQL file."""
        logger.debug(f"Reading schema file: {schema_file}")
        with open(schema_file) as f:
            schema_sql = f.read()

        cursor = self.conn.cursor()
        try:
            logger.debug("Executing schema SQL...")
            cursor.execute(schema_sql)
            self.conn.commit()
            logger.info("✅ Database schema initialized successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Schema initialization error: {e}")
            raise
        finally:
            cursor.close()
