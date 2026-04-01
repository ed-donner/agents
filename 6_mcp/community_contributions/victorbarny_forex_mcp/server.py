from __future__ import annotations

import json
from typing import Any, Optional

import requests
from mcp.server.fastmcp import FastMCP

FRANKFURTER_V2 = "https://api.frankfurter.dev/v2"

mcp = FastMCP("victorbarny_forex")


def _validate_iso4217(code: str) -> str:
    c = (code or "").strip().upper()
    if len(c) != 3 or not c.isalpha():
        raise ValueError(f"Invalid currency code {code!r}; use a 3-letter ISO 4217 code (e.g. USD, EUR).")
    return c


def _http_get_json(url: str, params: Optional[dict[str, Any]] = None) -> Any:
    r = requests.get(url, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


@mcp.tool()
async def get_latest_rates(base: str, symbols: str) -> str:
    """Return latest exchange rates from a base currency to one or more quote currencies (Frankfurter v2).

    Args:
        base: ISO 4217 currency code for the base (e.g. USD, EUR).
        symbols: Comma-separated quote currency codes (e.g. EUR,GBP,JPY).
    """
    b = _validate_iso4217(base)
    raw = (symbols or "").strip()
    if not raw:
        raise ValueError("Provide at least one quote currency in symbols (e.g. EUR,GBP).")
    quotes = [_validate_iso4217(x) for x in raw.split(",")]
    quotes_param = ",".join(quotes)
    data = _http_get_json(
        f"{FRANKFURTER_V2}/rates",
        params={"base": b, "quotes": quotes_param},
    )
    return json.dumps(data, indent=2)


@mcp.tool()
async def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    date: Optional[str] = None,
) -> str:
    """Convert an amount from one currency to another using the ECB-based rate (optional historical date).

    Args:
        amount: Amount to convert (must be non-negative).
        from_currency: Source ISO 4217 code.
        to_currency: Target ISO 4217 code.
        date: Optional calendar date YYYY-MM-DD for a historical rate; omit for latest.
    """
    if amount < 0:
        raise ValueError("amount must be non-negative.")
    f = _validate_iso4217(from_currency)
    t = _validate_iso4217(to_currency)
    if f == t:
        payload = {
            "amount": amount,
            "from": f,
            "to": t,
            "converted": amount,
            "rate": 1.0,
            "date": None,
        }
        return json.dumps(payload, indent=2)

    params: dict[str, str] = {}
    if date is not None and str(date).strip():
        params["date"] = str(date).strip()

    data = _http_get_json(f"{FRANKFURTER_V2}/rate/{f}/{t}", params=params if params else None)
    rate = float(data["rate"])
    converted = round(amount * rate, 6)
    out = {
        "amount": amount,
        "from": data.get("base", f),
        "to": data.get("quote", t),
        "rate": rate,
        "converted": converted,
        "date": data.get("date"),
    }
    return json.dumps(out, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
