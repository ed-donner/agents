# Fixed a couple issues in the capstone trader project

The capstone trader project is a fantastic project.   It has 6 MCP servers & 41 tools in its pay version and 6 MCP servers & 16 tools in its free version.  It has production-grade sleek Gradio UI and it is using best practice: prompts, instructions and MCP params are all configured externally instead of hard-coding.  It's using async (non-blocking) operation.  Also it's using ContextManager to ensure all resources are released and reclaimed. However, it does requires some refinement.

### Got "NOT_AUTHORIZED" error from Polygon API if running 'trader' when it's one day ahead in UTC time than New York time:

Would receive an error like

```
{"status":"NOT_AUTHORIZED","request_id":"4112e292da4a479d944dc2c4fcbf17c7","message":"Attempted to request today's data before end of day. Please upgrade your plan at https://polygon.io/pricing"}
```

it's due to the code block below.

```
def get_all_share_prices_polygon_eod() -> dict[str, float]:   
    probe = client.get_previous_close_agg("SPY")[0]
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
```

The cutoff of 'get\_previous\_close\_agg'  is UTC time.  'get\_grouped\_daily\_aggs' is checking using a trading date which is NYC time. There is 4 or 5 hours lag depending upon if daylight saving is involved (Currently it's 5 hours lag/ gap).

Before Jan 1, 2026, 0:00am UTC time (Dec. 31, 2025, 7:00pm New-York time) , I got the followings in 'get\_previous\_close\_agg' call

```
PreviousCloseAgg(timestamp=1767128400000......)
```

After that, I would receive the followings in 'get_previous_close_agg'

```
PreviousCloseAgg(timestamp=1767214800000......)
```

The former is December 30, 2025 9:00:00 PM (GMT),  4:00:00 PM (EST)  and the latter is December 31, 2025 9:00:00 PM (GMT),  4:00:00 PM (EST).   It's using trading closing time.   Therefore, 'last\_close' will flip to '2025-12-31' at December 31, 2025 7:00:00 PM, New York time.  However, the trading day of December 31 is NOT over yet. Hereby, I CANNOT call `get_grouped_daily_aggs` using '2025-12-31' until 5 hours later.  I am thinking about calling `get_grouped_daily_aggs` using current NY time - 1.  However, it might not be a trading date. Actually, that might overkill because the timestamp from 'get_previous_close_agg' works for most of the time except when calling during the gap mentioned above.  I changed 'get_all_share_prices_polygon_eod' as the following

```
def get_all_share_prices_polygon_eod(today_ny) -> dict[str, float]:
    """With much thanks to student Reema R. for fixing the timezone issue with this!"""
    client = RESTClient(polygon_api_key)
    probe = client.get_previous_close_agg("SPY")[0]
    # timestamp is the trading-closing timestamp. That's NYC 4:00pm and UTC 9:00pm. An example is 1767214800000
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=ZoneInfo("America/New_York")).date()
    if last_close == today_ny:
        last_close -= timedelta(days=1)
    # get_grouped_daily_aggs is using the trading date (NY time) as the cutoff
    while True:  
        results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
        if results:
            return {result.ticker: result.close for result in results}
        last_close -= timedelta(days=1)
```

Subtract 1 day only if `last_close` and `today_ny` is the same date.  That falls in the gap I mentioned above.  It is possible that the day before 'last_close' date is not a trading date. Include a loop to ensure that we will get a valid result from a real trading date.  Also notice that I am using 'tz=ZoneInfo("America/New_York")'.  That will take care of daylight saving or not for me.  I verified that the  change work in all 3 cases:

1) when the market open
2) during the 5 hour gap
3) after a new trading date start in N.Y.

### `get_share_price` kept getting 'market' table does not exist error after I deleted account.db

`with sqlite3.connect(DB) as conn` in the front of 'database.py' is supposed to execute before I call any function/ def in database.py.  It did not. I kept getting that error. The funny thing is that account.db was created after the call but just not before `get_share_price` call.  I added `class` and `__init__` to ensure tables were created before any functions.  Yes, market.py, accounts.py and tracers.py all initialize Database object first.

```
class Database:
    def __init__(self):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    datetime DATETIME,
                    type TEXT,
                    message TEXT
                )
            ''')
            cursor.execute('CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)')
            conn.commit()
```

### I kept getting Error: Max turns (10) exceeded on `Researcher` even though MAX_TURNS = 30 is configured

```
An error occurred while running the tool. Please try again. Error: Max turns (10) exceeded
```

I kept getting the above errors in multiple 'trader' logs.  10 is the default max_turn if not set.  Notice that we passed 'MAX_TURNS'  to 'trader' agent

```
await Runner.run(self.agent, message, max_turns=MAX_TURNS)
```

**The above only regulates 'trader' agent but not 'researcher` agent.**  Runner is not running 'researcher' agent directly and 'researcher' agent run indirectly as a tool for 'trader' agent.  We can regulate the max_turn on the tool.

```
async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool(), max_turns=MAX_TURNS)
```

# Github Codes:

https://github.com/threecuptea/agents
