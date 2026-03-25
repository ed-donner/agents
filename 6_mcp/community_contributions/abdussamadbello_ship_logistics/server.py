"""
MCP server: synthetic ship logistics (weather/route risk, security, alerts, fuel).
"""

from mcp.server.fastmcp import FastMCP

import ship_logistics as sl

mcp = FastMCP("ship_logistics")


@mcp.tool()
async def get_route_snapshot(origin_port_id: str, dest_port_id: str) -> dict:
    """Synthetic transit snapshot: distance, typical days, weather risk band, seasonal note.

    Args:
        origin_port_id: UN/LOCODE-style id, e.g. SGSIN, NLRTM, USLAX, AEJEA, CNYTN
        dest_port_id: Same format as origin
    """
    return sl.get_route_snapshot(origin_port_id, dest_port_id)


@mcp.tool()
async def get_security_advisory(region_code: str) -> dict:
    """Maritime security advisory stub (piracy/conflict-style index) for a named region.

    Args:
        region_code: One of RED_SEA, GULF_GUINEA, MALACCA, HORN_AFRICA
    """
    return sl.get_security_advisory(region_code)


@mcp.tool()
async def list_security_regions() -> list[str]:
    """List region codes available for get_security_advisory."""
    return sl.list_security_regions()


@mcp.tool()
async def list_active_alerts() -> list[dict]:
    """Synthetic corridor / compliance / weather-style alerts for demos."""
    return sl.list_active_alerts()


@mcp.tool()
async def get_fuel_price_index(ref_region: str) -> dict:
    """Synthetic VLSFO-style bunker index ($/mt) and 7d trend % for a region.

    Args:
        ref_region: SINGAPORE, ROTTERDAM, FUJAIRAH, USGC (aliases: SG, EU, ME, US)
    """
    return sl.get_fuel_price_index(ref_region)


@mcp.tool()
async def estimate_voyage_cost_stub(
    distance_nm: float,
    days: float,
    fuel_region: str = "SINGAPORE",
    daily_opex_usd: float = 12000,
    consumption_mt_per_day: float = 35,
) -> dict:
    """Rough bunker + daily opex stub (no real fixture terms).

    Args:
        distance_nm: Nautical miles (informational; cost driven by days and consumption)
        days: Port-to-port days at sea
        fuel_region: Bunker price region
        daily_opex_usd: Charterer-style daily cost placeholder
        consumption_mt_per_day: Main fuel consumption per day
    """
    return sl.estimate_voyage_cost_stub(
        distance_nm, days, fuel_region, daily_opex_usd, consumption_mt_per_day
    )


@mcp.tool()
async def corridor_summary(origin_port_id: str, dest_port_id: str) -> dict:
    """One-shot: route snapshot + relevant security advisories + reference fuel row.

    Args:
        origin_port_id: Port code, e.g. SGSIN
        dest_port_id: Port code, e.g. NLRTM
    """
    return sl.corridor_summary(origin_port_id, dest_port_id)


@mcp.tool()
async def list_ports() -> list[str]:
    """Known synthetic port codes for this demo."""
    return sl.list_ports()


if __name__ == "__main__":
    mcp.run(transport="stdio")
