"""Estimate the refund amount for a cancelled booking.

Usage:
    python estimate_refund.py <original_price> <days_before_departure>

Arguments:
    original_price        Original ticket price in USD (e.g. 499)
    days_before_departure Number of days before departure (e.g. 10)
"""

import sys
import json


def estimate_refund(price: float, days_before: int) -> dict:
    if days_before < 0:
        return {"error": "days_before_departure cannot be negative"}
    if price <= 0:
        return {"error": "original_price must be positive"}

    if days_before >= 7:
        pct = 0.75
        rule = "7+ days before departure (75% refund)"
    elif days_before >= 2:
        pct = 0.40
        rule = "2-6 days before departure (40% refund)"
    else:
        pct = 0.0
        rule = "Within 48 hours of departure (no refund)"

    refund = round(price * pct, 2)
    return {
        "original_price": price,
        "days_before_departure": days_before,
        "refund_percentage": int(pct * 100),
        "refund_amount": refund,
        "rule_applied": rule,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: estimate_refund.py <price> <days_before>"}))
        sys.exit(1)

    try:
        price = float(sys.argv[1])
        days = int(sys.argv[2])
        result = estimate_refund(price, days)
        print(json.dumps(result))
    except (ValueError, IndexError) as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
