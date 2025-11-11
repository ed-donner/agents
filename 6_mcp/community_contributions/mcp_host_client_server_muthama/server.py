# server.py
from datetime import date, datetime, timedelta, timezone
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import RootModel
from typing import Dict, Any, Callable, List
import inspect
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date-time-mcp")

# Date/time tools
@mcp.tool()
def current_date() -> dict:
    "Return today's date in ISO 8601 format (YYYY-MM-DD)."
    return {"date": date.today().isoformat()}

@mcp.tool()
def current_time() -> dict:
    "Return the current UTC time in ISO 8601 format."
    return {"time": datetime.now(timezone.utc).isoformat()}

@mcp.tool()
def shift_date(base_date: str, days: int) -> dict:
    "Shift a given date by a number of days."
    d = datetime.fromisoformat(base_date).date()
    return {"shifted_date": (d + timedelta(days=days)).isoformat()}

@mcp.tool()
def days_between(start_date: str, end_date: str) -> dict:
    "Number of days between two dates."
    s = datetime.fromisoformat(start_date).date()
    e = datetime.fromisoformat(end_date).date()
    return {"days_between": (e - s).days}

@mcp.tool()
def weekday_of(date_str: str) -> dict:
    "Return the weekday name for a given date."
    d = datetime.fromisoformat(date_str).date()
    return {"weekday": d.strftime("%A")}

@mcp.tool()
def day_of_week(date_str: str) -> dict:
    "Return weekday number (0=Monday) and name."
    d = datetime.fromisoformat(date_str).date()
    return {"weekday_number": d.weekday(), "weekday_name": d.strftime("%A")}

@mcp.tool()
def iso_week_number(date_str: str) -> dict:
    "Return ISO week number for a date."
    d = datetime.fromisoformat(date_str).date()
    return {"week_number": d.isocalendar().week}

@mcp.tool()
def format_date(date_str: str, pattern: str = "%A, %d %B %Y") -> dict:
    "Format a date using a strftime pattern."
    d = datetime.fromisoformat(date_str).date()
    return {"formatted": d.strftime(pattern)}

@mcp.tool()
def to_timestamp(datetime_str: str) -> dict:
    "Convert ISO datetime to UNIX timestamp (seconds). Accepts 'Z' as UTC."
    dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    return {"timestamp": int(dt.timestamp())}

@mcp.tool()
def from_timestamp(timestamp: int) -> dict:
    "Convert a UNIX timestamp (seconds) back to an ISO 8601 UTC datetime."
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return {"datetime": dt.isoformat()}

@mcp.tool()
def next_weekday(reference_date: str, weekday_name: str) -> dict:
    """
    Find the next date (strictly after reference_date) matching weekday_name.
    Weekday names: Monday, Tuesday, ... Sunday
    """
    d = datetime.fromisoformat(reference_date).date()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if weekday_name not in weekdays:
        return {"error": f"Invalid weekday: {weekday_name}. Must be one of {weekdays}"}
    target_index = weekdays.index(weekday_name)
    days_ahead = (target_index - d.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_date = d + timedelta(days=days_ahead)
    return {"next_date": next_date.isoformat()}

TOOL_FUNCS: List[Callable] = [
    current_date,
    current_time,
    shift_date,
    days_between,
    weekday_of,
    day_of_week,
    iso_week_number,
    format_date,
    to_timestamp,
    from_timestamp,
    next_weekday,
]
TOOL_MAP = {fn.__name__: fn for fn in TOOL_FUNCS}


# FastAPI app
app = FastAPI(title="Date/Time MCP Server (explicit registry)")

class Payload(RootModel[Dict[str, Any]]):
    """Request body wrapper for arbitrary JSON object payloads."""
    pass

def _make_tool_entry(fn: Callable) -> Dict[str, Any]:
    sig = inspect.signature(fn)
    params = {}
    required: List[str] = []
    for name, p in sig.parameters.items():
        ann = p.annotation
        ptype = "string"
        if ann in (int, float):
            ptype = "number"
        elif ann is bool:
            ptype = "boolean"
        elif ann == dict or ann == Dict:
            ptype = "object"
        elif ann == list or getattr(ann, "__origin__", None) == list:
            ptype = "array"
        params[name] = {"type": ptype}
        if p.default is inspect._empty:
            required.append(name)
    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip(),
        "input_schema": {"type": "object", "properties": params, **({"required": required} if required else {})},
        "output_schema": {"type": "object"},
    }

@app.get("/manifest.json")
def manifest():
    tools = [_make_tool_entry(fn) for fn in TOOL_FUNCS]
    return {"name": getattr(mcp, "name", "date-time-mcp"), "version": "1.0.0", "tools": tools}

def _invoke_function(fn: Callable, payload: Dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be an object")
    try:
        return fn(**payload)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Argument error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution error: {e}")

@app.post("/tools/{tool_name}")
def invoke(tool_name: str, payload: Payload):
    body = payload.root or {}
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return _invoke_function(fn, body)

@app.get("/healthz")
def health():
    return {"status": "ok", "tool_count": len(TOOL_FUNCS)}

@app.get("/routes")
def routes():
    return [route.path for route in app.routes]

if __name__ == "__main__":
    print("Starting server. Exposed tools:", list(TOOL_MAP.keys()))
    uvicorn.run(app, host="0.0.0.0", port=8000)
