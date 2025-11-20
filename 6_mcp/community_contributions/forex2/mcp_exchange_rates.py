"""
MCP server : mcp_exchange_rates.py

Used for start of day exchange rates for USD to requested currency

Get free api key from exchangerate-api.com
for start of day exchange rates
Load into .env file
as EXCHANGE_RATE_API_KEY=<<key from exchangerate-api.com >>

Usage:

@mcp.tool()
async def lookup_usd_exchange_rate(exchange_rate_symbol: str) -> float:
    This tool provides the current price of the given exchange for currency code per USD.
    Args:
        exchange_rate_symbol string of exchange_rate_symbol: e.g. the 
        AUSsymbol of the currency to get the exchange rate for example AUD for Australian dollars
    Returns: ExchangeRateResponse structured output
"""

from ast import Dict
import requests
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_exchange_rates_server.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

# Create logger for your MCP server
logger = logging.getLogger('mcp_exchange_rates_server')

class ExchangeRateResponse(BaseModel):
    """Structured response for exchange rate data"""
    base_currency: str = Field(..., description="Base currency (e.g., USD)")
    target_currency: str = Field(..., description="Target currency (e.g., AUD)")
    exchange_rate: Decimal = Field(..., description="Exchange rate value")
    timestamp: datetime = Field(..., description="When the rate was retrieved")
    source: str = Field(..., description="Data source (e.g., API provider)")
    last_updated: Optional[str] = Field(None, description="When the rate was last updated by source")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# MCP server to return USD exhcnage rate for a given currency code
# FROM exchangerate-api.com
# URL for GET:
#  https://v6.exchangerate-api.com/v6/YOUR-API-KEY/latest/USD
# Usage

load_dotenv(override=True)

mcp = FastMCP("market_server")
logger.info(f"starting exchange rate server")

api_key = os.getenv("EXCHANGE_RATE_API_KEY")
if not api_key:
        logger.error("EXCHANGE_RATE_API_KEY not found in environment")
        logger.info("Please set EXCHANGE_RATE_API_KEY in your .env file or environment")
    
logger.info(f"API Key: {api_key[:5]}...")
def get_exchange_rate(to_currency: str) -> ExchangeRateResponse:
    """Extract exchange rate from USD to to_currency specified currency"""
    try:
# Where USD is the base currency you want to use
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'
        logger.info(f"URL: {url}")
        # Making our request
        response = requests.get(url)
        logger.info(f"Response: {response}")
        data = response.json()
    except (KeyError, TypeError) as e:
        print(f"Error extracting rate: {e}")
        logger.error(f"Error extracting rate: {e}")
        return None
#

    """Extract exchange rate from USD to specified currency in structured output"""
    try:
        if data["result"] == "success":
         #   return data["conversion_rates"][to_currency]
            return ExchangeRateResponse(
                base_currency="USD",
                target_currency=to_currency,
                exchange_rate=Decimal(data["conversion_rates"][to_currency]),
                timestamp=datetime.now(),
                source="exchangerate-api.com",  
                last_updated=data["time_last_update_utc"]
            )
        else:
            return f"API returned error: {data.get('result')}"
    except (KeyError, TypeError) as e:
        return f"Error extracting rate: {e}"

@mcp.tool()
async def lookup_usd_exchange_rate(exchange_rate_symbol: str) -> float:
    """This tool provides the current price of the given exchange for currency code per USD.
    Args:
        exchange_rate_symbol string of currency_symbol: the symbol of the currency to get the exchange rate for example AUD
    """
    try:
        logger.info(f"Looking up exchange rate for {exchange_rate_symbol} {type(exchange_rate_symbol)}")
        # currency_symbol = exchange_rate_symbol["exchange_rate_symbol"]
        currency_symbol = exchange_rate_symbol
        logger.info(f"Currency symbol: {currency_symbol}")
        rate = get_exchange_rate(currency_symbol)
        logger.info(f"Rate: {rate}")
        return rate
        
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to get exchange rate for {exchange_rate_symbol}: {e}", exc_info=True)
        return f"Error extracting rate: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')