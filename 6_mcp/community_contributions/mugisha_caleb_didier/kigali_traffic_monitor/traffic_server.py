import os
import json
import asyncio
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from constants import KIGALI_SEGMENTS, KIGALI_BBOX

load_dotenv(override=True)

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

mcp = FastMCP("kigali_traffic")


def _clean_error(e: Exception) -> str:
    """Remove API key from error messages."""
    return str(e).replace(TOMTOM_API_KEY, "***")


async def _check_segment(client: httpx.AsyncClient, segment: dict) -> dict:
    """Check a single segment's traffic via two routing calls."""
    coords = segment["coordinates"]
    origin = f"{coords[0][0]},{coords[0][1]}"
    dest = f"{coords[-1][0]},{coords[-1][1]}"
    route_url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin}:{dest}/json"

    try:
        params = {"key": TOMTOM_API_KEY, "travelMode": "car", "routeType": "fastest"}

        live = await client.get(route_url, params={**params, "traffic": "true"})
        live.raise_for_status()
        live_secs = live.json()["routes"][0]["summary"]["travelTimeInSeconds"]

        await asyncio.sleep(0.3)

        base = await client.get(route_url, params={**params, "traffic": "false"})
        base.raise_for_status()
        base_secs = base.json()["routes"][0]["summary"]["travelTimeInSeconds"]

        delay = max(0, live_secs - base_secs)
        ratio = live_secs / base_secs if base_secs > 0 else 1.0

        if ratio < 1.1:
            level = "free_flow"
        elif ratio < 1.3:
            level = "light"
        elif ratio < 1.6:
            level = "moderate"
        else:
            level = "heavy"

        return {
            "segment_id": segment["id"],
            "road_name": segment["name"],
            "live_travel_time_secs": live_secs,
            "base_travel_time_secs": base_secs,
            "delay_secs": delay,
            "delay_minutes": round(delay / 60, 1),
            "congestion_ratio": round(ratio, 2),
            "congestion_level": level,
        }
    except Exception as e:
        return {"segment_id": segment["id"], "road_name": segment["name"], "error": _clean_error(e)}


@mcp.tool()
async def check_all_segments() -> dict:
    """Check traffic conditions on all 6 monitored Kigali road segments.
    Returns results for every segment in one call. Uses rate limiting internally
    to avoid hitting API limits.
    """
    results = []
    async with httpx.AsyncClient(timeout=20) as client:
        for segment in KIGALI_SEGMENTS:
            result = await _check_segment(client, segment)
            results.append(result)
            await asyncio.sleep(0.3)
    return {"segments": results}


@mcp.tool()
async def get_traffic_flow(segment_id: str) -> dict:
    """Get traffic conditions for a single Kigali road segment.
    Use check_all_segments to check all roads at once.

    Args:
        segment_id: The road segment identifier, e.g. 'kn5-downtown'
    """
    segment = next((s for s in KIGALI_SEGMENTS if s["id"] == segment_id), None)
    if not segment:
        return {"error": f"Unknown segment: {segment_id}", "segment_id": segment_id}
    async with httpx.AsyncClient(timeout=15) as client:
        return await _check_segment(client, segment)


@mcp.tool()
async def get_incidents() -> dict:
    """Get active traffic incidents in the Kigali area including accidents, road works and closures."""
    try:
        fields = json.dumps({
            "incidents": {
                "type": True,
                "properties": {
                    "iconCategory": True,
                    "magnitudeOfDelay": True,
                    "description": True,
                    "delay": True,
                    "roadNumbers": True,
                },
            }
        })
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.tomtom.com/traffic/services/5/incidentDetails?bbox={KIGALI_BBOX}&key={TOMTOM_API_KEY}&language=en-US",
                params={"fields": fields},
            )
            resp.raise_for_status()
            data = resp.json()
            incidents = data.get("incidents", [])
            if not incidents:
                return {"incidents": [], "message": "No active incidents in Kigali"}
            return {"incidents": incidents}
    except Exception as e:
        return {"incidents": [], "error": _clean_error(e)}


@mcp.resource("kigali://segments")
async def read_segments() -> str:
    """List of all monitored road segments in Kigali with their IDs, names and coordinates."""
    return json.dumps(KIGALI_SEGMENTS, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
