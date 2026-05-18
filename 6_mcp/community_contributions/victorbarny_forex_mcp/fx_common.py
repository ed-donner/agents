

from __future__ import annotations

import json
from typing import Any, Optional

import requests

FRANKFURTER_V2 = "https://api.frankfurter.dev/v2"


def validate_iso4217(code: str) -> str:
    c = (code or "").strip().upper()
    if len(c) != 3 or not c.isalpha():
        raise ValueError(f"Invalid currency code {code!r}; use a 3-letter ISO 4217 code (e.g. USD, EUR).")
    return c


def http_get_json(url: str, params: Optional[dict[str, Any]] = None) -> Any:
    r = requests.get(url, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


async def get_latest_rates(base: str, symbols: str) -> str:
    """Return latest exchange rates (Frankfurter v2)."""
    b = validate_iso4217(base)
    raw = (symbols or "").strip()
    if not raw:
        raise ValueError("Provide at least one quote currency in symbols (e.g. EUR,GBP).")
    quotes = [validate_iso4217(x) for x in raw.split(",")]
    quotes_param = ",".join(quotes)
    data = http_get_json(
        f"{FRANKFURTER_V2}/rates",
        params={"base": b, "quotes": quotes_param},
    )
    return json.dumps(data, indent=2)


async def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    date: Optional[str] = None,
) -> str:
    """Convert amount using ECB-based rate; optional historical date YYYY-MM-DD."""
    if amount < 0:
        raise ValueError("amount must be non-negative.")
    f = validate_iso4217(from_currency)
    t = validate_iso4217(to_currency)
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

    data = http_get_json(f"{FRANKFURTER_V2}/rate/{f}/{t}", params=params if params else None)
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
