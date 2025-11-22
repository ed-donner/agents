# src/prism/tools/database_tools.py
from crewai.tools import tool

from ..database.connection import DatabaseConnection
from ..utils import logger


@tool("Get All Positions")
def get_all_positions():
    """Fetch all trader swap positions from database."""
    logger.info("Fetching all swap positions from database")
    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT position_id, trade_date, maturity_date, notional,
               fixed_rate, float_index, pay_receive, currency
        FROM swap_positions
        ORDER BY trade_date DESC
    """

    positions = db.execute_query(query)
    db.close()

    logger.info(f"Retrieved {len(positions)} positions")
    return positions


@tool("Get Position By ID")
def get_position_by_id(position_id: str):
    """Fetch a specific swap position by ID."""
    logger.debug(f"Fetching position: {position_id}")
    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT * FROM swap_positions WHERE position_id = %s
    """

    position = db.execute_query(query, (position_id,))
    db.close()

    return position[0] if position else None


@tool("Insert Trade Signal")
def insert_trade_signal(
    position_id: str,
    signal_type: str,
    current_pnl: float,
    reason: str,
    recommended_action: str,
):
    """Insert a trade signal into the database."""
    # Remove the "if signal_type == 'CLOSE'" check - insert everything
    db = DatabaseConnection()
    db.connect()

    insert_query = """
        INSERT INTO trade_signals (position_id, signal_type, current_pnl, reason, recommended_action, timestamp, executed)
        VALUES (%s, %s, %s, %s, %s, NOW(), FALSE)
    """

    db.execute_query(
        insert_query,
        (position_id, signal_type, current_pnl, reason, recommended_action),
    )
    db.close()

    logger.info(f"✅ Signal inserted: {position_id} - {signal_type}")
    return f"Signal {signal_type} recorded for {position_id}"
