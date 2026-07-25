"""
Timezone MCP based server.
"""

from datetime import datetime
import pytz
from dateutil import parser as date_parser
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

# Initialize FastMCP server
mcp = FastMCP("timezone_server")


@mcp.tool()
async def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in a specific IANA timezone.

    Args:
        timezone: The IANA timezone name (e.g., 'Africa/Lagos', 'America/New_York').
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except pytz.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'"


@mcp.tool()
async def convert_time(datetime_str: str, from_tz: str, to_tz: str) -> str:
    """Convert a date/time string from one timezone to another.

    Args:
        datetime_str: The date/time string to convert (e.g., '2024-03-27 15:00').
        from_tz: The source IANA timezone.
        to_tz: The target IANA timezone.
    """
    try:
        source_tz = pytz.timezone(from_tz)
        target_tz = pytz.timezone(to_tz)

        # Parse the input time string
        dt = date_parser.parse(datetime_str)

        # If naive, assume it's in source_tz
        if dt.tzinfo is None:
            dt = source_tz.localize(dt)
        else:
            # If already aware, convert to source_tz
            dt = dt.astimezone(source_tz)

        converted_dt = dt.astimezone(target_tz)
        return converted_dt.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def list_iana_timezones() -> List[str]:
    """List all available IANA timezones supported by this server."""
    return pytz.all_timezones


@mcp.tool()
async def get_timezone_info(timezone: str) -> Dict:
    """Get detailed information about a timezone (offset, DST status, abbreviation).

    Args:
        timezone: The IANA timezone name.
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return {
            "timezone": timezone,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "offset": now.strftime("%z"),
            "abbreviation": now.strftime("%Z"),
            "is_dst": bool(now.dst()),
            "utc_offset_hours": now.utcoffset().total_seconds() / 3600,
        }
    except pytz.UnknownTimeZoneError:
        return {"error": f"Unknown timezone '{timezone}'"}


@mcp.tool()
async def calculate_time_diff(tz1: str, tz2: str) -> str:
    """Calculate the time difference in hours between two timezones.

    Args:
        tz1: The first IANA timezone.
        tz2: The second IANA timezone.
    """
    try:
        t1 = pytz.timezone(tz1)
        t2 = pytz.timezone(tz2)

        now = datetime.now()
        offset1 = t1.localize(now).utcoffset().total_seconds() / 3600
        offset2 = t2.localize(now).utcoffset().total_seconds() / 3600

        diff = offset2 - offset1
        return f"The difference between {tz1} and {tz2} is {diff:+} hours."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_next_dst_transition(timezone: str) -> str:
    """Find the next Daylight Saving Time transition for a given timezone.

    Args:
        timezone: The IANA timezone name.
    """
    try:
        tz = pytz.timezone(timezone)
        if not hasattr(tz, "_utc_transition_times"):
            return f"Timezone {timezone} does not have recorded DST transitions."

        now = datetime.utcnow()
        for trans in tz._utc_transition_times:
            if trans > now:
                # Find the corresponding transition in localized time
                localized_trans = pytz.utc.localize(trans).astimezone(tz)
                return f"Next transition in {timezone}: {localized_trans.strftime('%Y-%m-%d %H:%M:%S %Z')}"

        return f"No upcoming DST transitions found for {timezone}."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def is_valid_timezone_name(name: str) -> bool:
    """Validate if a string is a valid IANA timezone name.

    Args:
        name: The string to validate.
    """
    return name in pytz.all_timezones_set


@mcp.tool()
async def get_timezones_by_offset_hours(offset_hours: float) -> List[str]:
    """Find all IANA timezones that match a specific UTC offset in hours.

    Args:
        offset_hours: The UTC offset in hours (e.g., 1.0 or 5.5).
    """
    matches = []
    now = datetime.now()
    for tz_name in pytz.all_timezones:
        tz = pytz.timezone(tz_name)
        if tz.localize(now).utcoffset().total_seconds() / 3600 == offset_hours:
            matches.append(tz_name)
    return matches


@mcp.tool()
async def format_local_time(
    datetime_str: str, timezone: str, format_pattern: str = "%A, %B %d, %Y %I:%M %p"
) -> str:
    """Format a date/time string into a human-readable local format for a specific timezone.

    Args:
        datetime_str: The date/time string to format.
        timezone: The IANA timezone.
        format_pattern: Strftime-compatible format string.
    """
    try:
        tz = pytz.timezone(timezone)
        dt = date_parser.parse(datetime_str)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt).astimezone(tz)
        else:
            dt = dt.astimezone(tz)

        return dt.strftime(format_pattern)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_utc_now() -> str:
    """Get the current UTC time in high precision."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@mcp.resource("timezone://iana_list")
async def list_timezones_resource() -> str:
    """A resource providing the full list of IANA timezones as a string."""
    return "\n".join(pytz.all_timezones)


if __name__ == "__main__":
    mcp.run(transport="stdio")
