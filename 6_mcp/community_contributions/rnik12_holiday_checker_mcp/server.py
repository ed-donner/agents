from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Dependency: python-holidays
# Install once from repo root:  cd 6_mcp && uv add holidays
import holidays

mcp = FastMCP("holiday_checker_mcp")


class CheckArgs(BaseModel):
    country: str = Field(description="Country code or name, e.g. 'US', 'United States', 'IN', 'India'")
    state: Optional[str] = Field(default=None, description="Optional state/province code or name, e.g. 'CA', 'California'")
    city: Optional[str] = Field(default=None, description="Optional city (for display only)")
    start_date: str = Field(description="Inclusive start date, YYYY-MM-DD")
    end_date: str = Field(description="Inclusive end date, YYYY-MM-DD")


def _parse_date(iso: str):
    return datetime.strptime(iso, "%Y-%m-%d").date()


def _resolve_country(country: str):
    # Try direct lookup (codes or names). Fallback to explicit match.
    try:
        return holidays.country_holidays(country)
    except Exception:
        for key in holidays.list_supported_countries():
            if key.lower() == country.lower():
                return holidays.country_holidays(key)
    raise ValueError(
        f"Unsupported country '{country}'. Try an ISO code like 'US', 'IN', 'GB', or a supported name."
    )


@mcp.tool()
def check_holidays(args: CheckArgs) -> List[Dict]:
    """
    Return holidays between start_date and end_date (inclusive) for the given location.
    City is informational only; country/state determine the calendar if available.
    """
    cal = _resolve_country(args.country)

    # Optional state/province subdivision
    if args.state:
        # Try the given state as-is; then TitleCase fallback (some countries use names)
        try:
            cal = holidays.country_holidays(cal.country, subdiv=args.state)
        except Exception:
            try:
                cal = holidays.country_holidays(cal.country, subdiv=args.state.title())
            except Exception:
                # If not supported, continue without subdivision
                pass

    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)
    if end < start:
        raise ValueError("end_date must be on/after start_date")

    out: List[Dict] = []
    d = start
    while d <= end:
        name = cal.get(d)
        if name:
            out.append(
                {
                    "date": d.isoformat(),
                    "name": str(name),
                    "country": cal.country,
                    "state": args.state,
                    "city": args.city,
                }
            )
        d += timedelta(days=1)
    return out


@mcp.tool()
def is_holiday(country: str, date: str, state: Optional[str] = None) -> Dict:
    """
    Quick boolean check for a single date.
    """
    cal = _resolve_country(country)
    if state:
        try:
            cal = holidays.country_holidays(cal.country, subdiv=state)
        except Exception:
            try:
                cal = holidays.country_holidays(cal.country, subdiv=state.title())
            except Exception:
                pass
    d = _parse_date(date)
    name = cal.get(d)
    return {"date": d.isoformat(), "is_holiday": bool(name), "name": str(name) if name else None}


@mcp.resource("holidays://calendar/{country}/{year}")
def get_calendar(country: str, year: str) -> str:
    """
    Return a newline list of YYYY-MM-DD — Holiday Name for the whole year.
    """
    y = int(year)
    cal = _resolve_country(country)
    rows = [f"{dt.isoformat()} — {nm}" for dt, nm in sorted(cal.items(years=y))]
    return "\n".join(rows)


if __name__ == "__main__":
    mcp.run(transport="stdio")
