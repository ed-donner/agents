from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random
from database import Database
from functools import lru_cache
from zoneinfo import ZoneInfo

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

is_paid_polygon = polygon_plan == "paid"
is_realtime_polygon = polygon_plan == "realtime"

db = Database()



def is_market_open() -> bool:
    client = RESTClient(polygon_api_key)
    market_status = client.get_market_status()
    return market_status.market == "open"


def get_all_share_prices_polygon_eod(today_ny) -> dict[str, float]:
    """With much thanks to student Reema R. for fixing the timezone issue with this!"""
    client = RESTClient(polygon_api_key)
    probe = client.get_previous_close_agg("SPY")[0]
    # timestamp is the trading-closing timestamp. That's NYC 4:00pm and UTC 9:00pm. An example is 1767214800000
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=ZoneInfo("America/New_York")).date()
    if last_close == today_ny:
        last_close -= timedelta(days=1)
        # we would receive
        # {"status":"NOT_AUTHORIZED","request_id":"4112e292da4a479d944dc2c4fcbf17c7","message":"Attempted to request today's data before end of day. 
        # Please upgrade your plan at https://polygon.io/pricing"} in that case
        # `get_previous_close_agg` will flip to 12/31 after UTC midnight (2026-01-01), However, we cannot call get_grouped_daily_aggs using 12/31 until
        # we are passing 12/31 midnight NY time (trading date).  There is 4 or 5 hour of gap.  
        # Subtract 1 day in that case.  However, the date before last_close might not be a trading date. That's why we need to be in a loop 
        # We can depend upon the timestamp from get_previous_close_agg for most of the time except when calling during the gap mentioned above
    # get_grouped_daily_aggs is using the trading date (NY time) as the cutoff
    while True:  
        results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
        if results:
            return {result.ticker: result.close for result in results}
        last_close -= timedelta(days=1)

@lru_cache(maxsize=2)
def get_market_for_prior_date(today):
    today_ymd = today.strftime("%Y-%m-%d")
    market_data = db.read_market(today_ymd)
    if not market_data:
        market_data = get_all_share_prices_polygon_eod(today)
        db.write_market(today_ymd, market_data)
    return market_data


def get_share_price_polygon_eod(symbol) -> float:
    # ZoneInfo or pytz so that I don't need to worry about using EST or EDT 
    today = datetime.now(ZoneInfo("America/New_York")).date() # need to use date instead of date_time otherwise cache won't work
    market_data = get_market_for_prior_date(today)
    return float(market_data.get(symbol, 0.0))


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
    if polygon_api_key:
        try:
            return get_share_price_polygon(symbol)
        except Exception as e:
            print(f"Was not able to use the polygon API due to {e}; using a random number")
    return float(random.randint(1, 100))