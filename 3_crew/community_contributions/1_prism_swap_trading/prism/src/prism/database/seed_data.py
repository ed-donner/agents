# src/prism/database/seed_data.py
from .connection import DatabaseConnection


def seed_positions():
    """Insert sample swap positions for testing."""
    db = DatabaseConnection()
    db.connect()

    # Sample positions
    positions = [
        (
            "SWP001",
            "2024-01-15",
            "2029-01-15",
            10000000,
            4.25,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP002",
            "2024-03-20",
            "2034-03-20",
            25000000,
            4.50,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
        (
            "SWP003",
            "2024-06-10",
            "2029-06-10",
            15000000,
            4.10,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP004",
            "2024-08-05",
            "2027-08-05",
            8000000,
            3.95,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
    ]

    insert_query = """
        INSERT INTO swap_positions
        (position_id, trade_date, maturity_date, notional, fixed_rate, float_index, pay_receive, currency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (position_id) DO NOTHING
    """

    for position in positions:
        db.execute_query(insert_query, position)

    db.close()
    print(f"✅ Seeded {len(positions)} swap positions!")


if __name__ == "__main__":
    seed_positions()
