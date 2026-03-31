import os
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# --- Configuration & Logging ---
load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_exchange_rates_server.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mcp_exchange_rates_server')

API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
BASE_URL = "https://v6.exchangerate-api.com/v6"

# --- Simple In-Memory Cache ---
# Stores: { "BASE_CODE": {"timestamp": datetime, "rates": dict} }
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = timedelta(hours=1) 

class ExchangeRateResponse(BaseModel):
    """Structured response for exchange rate data"""
    base_currency: str
    target_currency: str
    exchange_rate: Decimal
    timestamp: datetime
    source: str = "exchangerate-api.com"
    last_updated_api: Optional[str]

# --- Core Logic ---
mcp = FastMCP("market_server")

async def fetch_rates(base_currency: str) -> Dict[str, Any]:
    """Fetch rates from API or return cached version if fresh."""
    base_currency = base_currency.upper()
    
    # 1. Check Cache
    if base_currency in _CACHE:
        cache_entry = _CACHE[base_currency]
        if datetime.now() - cache_entry["timestamp"] < CACHE_TTL:
            logger.info(f"Using cached rates for {base_currency}")
            return cache_entry["data"]

    # 2. Asynchronous Request
    if not API_KEY:
        raise ValueError("EXCHANGE_RATE_API_KEY is not set")

    url = f"{BASE_URL}/{API_KEY}/latest/{base_currency}"
    
    async with httpx.AsyncClient() as client:
        logger.info(f"Fetching fresh rates for {base_currency} from API")
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    if data.get("result") == "success":
        # 3. Update Cache
        _CACHE[base_currency] = {
            "timestamp": datetime.now(),
            "data": data
        }
        return data
    else:
        raise Exception(f"API Error: {data.get('error-type', 'Unknown error')}")

@mcp.tool()
async def lookup_exchange_rate(target_currency: str, base_currency: str = "USD") -> Dict[str, Any]:
    """
    Get the exchange rate between two currencies.
    Args:
        target_currency: The currency symbol to convert TO (e.g., JPY, EUR).
        base_currency: The currency symbol to convert FROM (defaults to USD).
    """
    try:
        target = target_currency.strip().upper()
        base = base_currency.strip().upper()
        
        data = await fetch_rates(base)
        rates = data.get("conversion_rates", {})

        if target not in rates:
            return {"error": f"Currency symbol '{target}' not found."}

        # Create structured response
        res = ExchangeRateResponse(
            base_currency=base,
            target_currency=target,
            exchange_rate=Decimal(str(rates[target])),
            timestamp=datetime.now(),
            last_updated_api=data.get("time_last_update_utc")
        )
        
        # Return as dict for MCP/LLM compatibility
        return res.model_dump()

    except Exception as e:
        logger.error(f"Exchange rate lookup failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_supported_currencies() -> list[str]:
    """Returns a list of all currency codes available in the cache."""
    if not _CACHE:
        await fetch_rates("USD") # Populate cache if empty
    return list(_CACHE["USD"]["data"]["conversion_rates"].keys())

if __name__ == "__main__":
    mcp.run(transport='stdio')