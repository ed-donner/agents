from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from functools import lru_cache
import random
from database import write_market, read_market, get_simulation_date
from simulation import get_historical_price

load_dotenv(override=True)

polygon_api_key = os.getenv("MASSIVE_API_KEY")
polygon_plan = os.getenv("MASSIVE_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"


print(f"DEBUG: polygonn_api_key: {polygon_api_key is not None}")
print(f"DEBUG: polygon_plan: {polygon_plan}")
print(f"DEBUG: is_paid_polygon: {is_paid_polygon}, is_realtime_polygon: {is_realtime_polygon}")

def is_market_open() -> bool:
    client = RESTClient(polygon_api_key)
    market_status = client.get_market_status()
    return market_status.market == "open"


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    """With much thanks to student Reema R. for fixing the timezone issue with this!"""
    client = RESTClient(polygon_api_key)

    probe = client.get_previous_close_agg("SPY")[0]
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()

    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
    return {result.ticker: result.close for result in results}


@lru_cache(maxsize=2)
def get_market_for_prior_date(today):
    market_data = read_market(today)
    if not market_data:
        market_data = get_all_share_prices_polygon_eod()
        write_market(today, market_data)
    return market_data


def get_share_price_polygon_eod(symbol) -> float:
    today = datetime.now().date().strftime("%Y-%m-%d")
    market_data = get_market_for_prior_date(today)
    return market_data.get(symbol, 0.0)


def get_share_price_polygon_min(symbol) -> float:
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    return result.min.close or result.prev_day.close


def get_share_price_polygon(symbol) -> float:
    if is_paid_polygon:
        return get_share_price_polygon_min(symbol)
    else:
        return get_share_price_polygon_eod(symbol)


def get_share_price(symbol) -> float:
    sim_date = get_simulation_date()
    if sim_date:
        price = get_historical_price(sim_date, symbol, allow_api_fetch=True)
        
        if price is not None:
            return price
        
        # Symbol not available for this date
        print(f"Warning: No historical data for {symbol} on {sim_date}, using fallback")
        return float(random.randint(1, 100))
    
    if polygon_api_key:
        try:
            price = get_share_price_polygon(symbol)
            print(f"DEBUG: Got price for {symbol}: ${price}")
            return price 
        except Exception as e:
            print(f"DEBUG: Was not able to use the polygon API due to {e}; using a random number")
    return float(random.randint(1, 100))
