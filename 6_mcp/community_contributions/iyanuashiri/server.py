"""Frankfurter MCP server — Frankfurter v1 API (no API key).

Uses https://api.frankfurter.dev/v1/ (documented v1: base + symbols), same
contract as api.frankfurter.app/latest?from=&to= but without relying on the
legacy host/redirect. See https://www.frankfurter.dev/v1/
"""

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Official v1 base — matches e.g. GET .../v1/latest?base=USD&symbols=EUR
FRANKFURTER_V1 = "https://api.frankfurter.dev/v1"
USER_AGENT = "frankfurter-mcp/1.0"

mcp = FastMCP("frankfurter-mcp")


async def _frankfurter_get(path: str, params: dict[str, Any]) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    url = f"{FRANKFURTER_V1}{path}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params=params,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def _normalize_code(code: str) -> str | None:
    c = code.strip().upper()
    if len(c) != 3 or not c.isalpha():
        return None
    return c


@mcp.tool()
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies using live ECB-based rates.

    Args:
        amount: Amount in the source currency (must be >= 0).
        from_currency: Three-letter ISO 4217 code (e.g. USD, EUR, GBP).
        to_currency: Three-letter ISO 4217 code for the result.
    """
    if amount < 0:
        return "Amount must be non-negative."

    from_c = _normalize_code(from_currency)
    to_c = _normalize_code(to_currency)
    if not from_c or not to_c:
        return "Currency codes must be three letters (ISO 4217), e.g. USD, EUR."

    if from_c == to_c:
        return f"{amount} {from_c} = {amount} {to_c} (same currency)."

    data = await _frankfurter_get(
        "/latest", {"base": from_c, "symbols": to_c}
    )
    if not data or "rates" not in data:
        return (
            "Could not fetch exchange rates. "
            "Check that both currency codes are supported (use list_supported_currencies)."
        )

    rates = data["rates"]
    if to_c not in rates:
        return f"No rate returned for {from_c} → {to_c}."

    rate = float(rates[to_c])
    converted = amount * rate
    date = data.get("date", "unknown")
    return (
        f"{amount} {from_c} = {converted:.6g} {to_c}\n"
        f"Rate: 1 {from_c} = {rate} {to_c} (ECB via Frankfurter, date: {date})"
    )


@mcp.tool()
async def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Return the mid-market rate: how much target currency equals one unit of source.

    Args:
        from_currency: Three-letter ISO 4217 source currency code.
        to_currency: Three-letter ISO 4217 target currency code.
    """
    from_c = _normalize_code(from_currency)
    to_c = _normalize_code(to_currency)
    if not from_c or not to_c:
        return "Currency codes must be three letters (ISO 4217), e.g. USD, EUR."

    if from_c == to_c:
        return f"1 {from_c} = 1 {to_c} (same currency)."

    data = await _frankfurter_get(
        "/latest", {"base": from_c, "symbols": to_c}
    )
    if not data or "rates" not in data:
        return (
            "Could not fetch the rate. "
            "Check currency codes (use list_supported_currencies)."
        )

    rates = data["rates"]
    if to_c not in rates:
        return f"No rate for {from_c} → {to_c}."

    rate = float(rates[to_c])
    date = data.get("date", "unknown")
    return f"1 {from_c} = {rate} {to_c} (Frankfurter / ECB, date: {date})"


@mcp.tool()
async def list_supported_currencies() -> str:
    """List ISO 4217 currency codes supported by the Frankfurter API for conversion."""
    data = await _frankfurter_get("/currencies", {})
    if not data:
        return "Could not fetch the currency list."

    lines = [f"{code}: {name}" for code, name in sorted(data.items())]
    return "Supported currencies:\n" + "\n".join(lines)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
