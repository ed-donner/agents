from datetime import date, datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("date-time-mcp")


@mcp_server.tool()
def current_date() -> dict:
    """Return today's date in ISO 8601 format (YYYY-MM-DD)."""
    return {"date": date.today().isoformat()}


@mcp_server.tool()
def current_time() -> dict:
    """Return current UTC time in ISO 8601 format."""
    return {"datetime": datetime.now(timezone.utc).isoformat()}


@mcp_server.tool()
def shift_date(base_date: str, days: int) -> dict:
    """Shift a given ISO date string by a number of days."""
    d = datetime.fromisoformat(base_date).date()
    newd = d + timedelta(days=int(days))
    return {"date": newd.isoformat()}


@mcp_server.tool()
def days_between(start_date: str, end_date: str) -> dict:
    """Return number of days between two ISO dates (end - start)."""
    s = datetime.fromisoformat(start_date).date()
    e = datetime.fromisoformat(end_date).date()
    return {"days": (e - s).days}


@mcp_server.tool()
def weekday_of(date_str: str) -> dict:
    """Return weekday index (0=Monday..6=Sunday) for given ISO date."""
    d = datetime.fromisoformat(date_str).date()
    return {"weekday": d.weekday()}


@mcp_server.tool()
def day_of_week(date_str: str) -> dict:
    """Return weekday name for given ISO date (e.g., Monday)."""
    d = datetime.fromisoformat(date_str).date()
    return {"day": d.strftime('%A')}


@mcp_server.tool()
def iso_week_number(date_str: str) -> dict:
    """Return ISO week number and ISO year for a given ISO date."""
    d = datetime.fromisoformat(date_str).date()
    iso_year, iso_week, iso_weekday = d.isocalendar()
    return {"iso_year": iso_year, "iso_week": iso_week, "iso_weekday": iso_weekday}


@mcp_server.tool()
def format_date(date_str: str, fmt: str = "%Y-%m-%d") -> dict:
    """Format an ISO date using a provided strftime format string."""
    d = datetime.fromisoformat(date_str).date()
    return {"formatted": d.strftime(fmt)}


@mcp_server.tool()
def to_timestamp(date_str: str) -> dict:
    """Convert an ISO datetime string to UNIX timestamp (seconds)."""
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return {"timestamp": int(dt.timestamp())}


@mcp_server.tool()
def from_timestamp(ts: int) -> dict:
    """Convert UNIX timestamp (seconds) to ISO UTC datetime string."""
    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    return {"datetime": dt.isoformat()}


@mcp_server.tool()
def next_weekday(date_str: str, weekday: int) -> dict:
    """Given a date and target weekday (0=Monday..6=Sunday), return the next date with that weekday."""
    d = datetime.fromisoformat(date_str).date()
    days_ahead = (weekday - d.weekday()) % 7
    newd = d + timedelta(days=days_ahead)
    return {"date": newd.isoformat()}


if __name__ == "__main__":
    mcp_server.run(transport="stdio")
