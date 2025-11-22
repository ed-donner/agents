# src/prism/database/init_db.py
from pathlib import Path

from ..utils import logger
from .connection import DatabaseConnection
from .seed_data import seed_positions


def initialize_database():
    """Initialize the database with schema."""
    logger.info("🗄️ Initializing database...")

    db = DatabaseConnection()
    logger.debug("Connecting to database...")
    db.connect()

    schema_path = Path(__file__).parent / "schema.sql"
    logger.debug(f"Loading schema from: {schema_path}")

    logger.info("📋 Initializing database schema...")
    db.initialize_schema(schema_path)

    logger.debug("Closing database connection...")
    db.close()

    logger.info("✅ Database initialized successfully!")

    # Seed initial data
    logger.info("🌱 Seeding initial data...")
    seed_positions()
