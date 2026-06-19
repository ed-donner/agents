"""
MCP server: agronomy planning stubs (GDD, planting windows, soil water, rotation, briefs).

All outputs are synthetic or illustrative — not a substitute for agronomic advice.
"""

from __future__ import annotations

import json
from datetime import date

from mcp.server.fastmcp import FastMCP

import agronomy_core as ag

mcp = FastMCP("agronomy_advisor")


@mcp.tool()
async def list_agro_zones() -> list[str]:
    """List known agro-ecological zone codes (synthetic reference set)."""
    return ag.list_zones()


@mcp.tool()
async def list_crop_codes() -> list[str]:
    """List crop codes available for calculators (maize, wheat, tomato, etc.)."""
    return ag.list_crops()


@mcp.tool()
async def list_soil_texture_codes() -> list[str]:
    """List soil texture codes used by water-balance stubs."""
    return ag.list_soil_textures()


@mcp.tool()
async def compute_gdd_sum(
    zone_code: str,
    crop_code: str,
    start_date_iso: str,
    end_date_iso: str,
) -> dict:
    """Sum growing degree days (GDD) for a date range using zone typical temps.

    Args:
        zone_code: e.g. HRV-HIGH, SAV-MID, MED-COAST
        crop_code: e.g. maize, tomato
        start_date_iso: YYYY-MM-DD
        end_date_iso: YYYY-MM-DD
    """
    start = date.fromisoformat(start_date_iso)
    end = date.fromisoformat(end_date_iso)
    return ag.accumulate_gdd(zone_code, crop_code, start, end)


@mcp.tool()
async def planting_window_hint(crop_code: str, zone_code: str) -> dict:
    """Suggest a starting month and relate it to rainy seasons (heuristic, synthetic)."""
    return ag.suggest_planting_window(crop_code, zone_code)


@mcp.tool()
async def soil_water_snapshot(
    soil_texture: str,
    root_depth_m: float,
    last_rain_mm: float,
    days_since_rain: int,
    et0_mm_per_day: float,
) -> dict:
    """Rough root-zone water status from rain, ET0, and soil water holding (stub)."""
    return ag.soil_water_status(
        soil_texture, root_depth_m, last_rain_mm, days_since_rain, et0_mm_per_day
    )


@mcp.tool()
async def crop_rotation_score(previous_crop: str, next_crop: str) -> dict:
    """Score a two-crop sequence for diversification benefits (toy model)."""
    return ag.rotation_advice(previous_crop, next_crop)


@mcp.tool()
async def pest_risk_band(week_of_year: int, zone_code: str, crop_code: str) -> dict:
    """Synthetic seasonal pest-pressure index for scenario planning."""
    return ag.pest_pressure_stub(week_of_year, zone_code, crop_code)


@mcp.tool()
async def nutrient_placeholder(soil_ph: float, organic_matter_pct: float, crop_code: str) -> dict:
    """Placeholder NPK band commentary — always validate with soil tests locally."""
    return ag.nutrient_outline_stub(soil_ph, organic_matter_pct, crop_code)


@mcp.tool()
async def integrated_field_brief(
    zone_code: str,
    soil_texture: str,
    crop_code: str,
    area_ha: float,
) -> dict:
    """One-shot summary: planting hint, water demand scale, soil water snapshot."""
    return ag.field_brief(zone_code, soil_texture, crop_code, area_ha)


@mcp.resource("agronomy://catalog/crops", mime_type="application/json")
async def crop_catalog() -> str:
    """Full crop parameter catalog (JSON) for agents that need static reference."""
    return json.dumps(ag.CROPS, indent=2)


@mcp.resource("agronomy://catalog/zones", mime_type="application/json")
async def zone_catalog() -> str:
    """Agro-ecological zone metadata (JSON)."""
    return json.dumps(ag.ZONES, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
