# src/prism/tools/market_data_tools.py
from crewai.tools import tool

from ..database.connection import DatabaseConnection
from ..utils import logger


@tool("Store Market Rates")
def store_market_rates(rates: list):
    """Store market rates in database."""
    db = DatabaseConnection()
    db.connect()

    for rate in rates:
        # Strip % and convert to float if needed
        mid_rate = rate["mid_rate"]
        if isinstance(mid_rate, str):
            mid_rate = float(mid_rate.replace("%", ""))

        # Same for bid_rate and ask_rate
        bid_rate = rate.get("bid_rate", mid_rate - 0.01)
        if isinstance(bid_rate, str):
            bid_rate = float(bid_rate.replace("%", ""))

        ask_rate = rate.get("ask_rate", mid_rate + 0.01)
        if isinstance(ask_rate, str):
            ask_rate = float(ask_rate.replace("%", ""))

        insert_query = """
            INSERT INTO market_rates (tenor, currency, mid_rate, bid_rate, ask_rate, timestamp, source)
            VALUES (%s, %s, %s, %s, %s, NOW(), 'Serper')
        """
        db.execute_query(
            insert_query,
            (rate["tenor"], rate.get("currency", "USD"), mid_rate, bid_rate, ask_rate),
        )

    db.close()
    return f"Stored {len(rates)} rates"


@tool("Get Latest Market Rate")
def get_latest_market_rate(tenor: str, currency: str = "USD"):
    """Get the most recent market rate for a specific tenor."""
    logger.debug(f"🔍 Fetching latest {tenor} {currency} rate from database...")

    db = DatabaseConnection()
    db.connect()

    query = """
        SELECT mid_rate, bid_rate, ask_rate, timestamp
        FROM market_rates
        WHERE tenor = %s AND currency = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """

    result = db.execute_query(query, (tenor, currency))
    db.close()

    if result:
        logger.debug(f"  Found: {tenor} = {result[0]['mid_rate']}%")
    else:
        logger.warning(f"  No rate found for {tenor} {currency}")

    return result[0] if result else None
