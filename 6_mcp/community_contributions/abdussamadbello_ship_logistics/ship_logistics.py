"""
Synthetic maritime logistics data for demos and coursework.
Not for real navigation, chartering, or compliance decisions.
"""

from __future__ import annotations

from typing import Any

# --- Static reference data (synthetic) ---------------------------------

PORTS: dict[str, dict[str, Any]] = {
    "SGSIN": {"name": "Singapore", "region": "SEA", "lat": 1.29, "lon": 103.85},
    "NLRTM": {"name": "Rotterdam", "region": "NWE", "lat": 51.92, "lon": 4.48},
    "USLAX": {"name": "Los Angeles", "region": "USWC", "lat": 33.75, "lon": -118.27},
    "AEJEA": {"name": "Jebel Ali", "region": "MEG", "lat": 25.01, "lon": 55.06},
    "CNYTN": {"name": "Yantian", "region": "CHN", "lat": 22.57, "lon": 114.27},
}

# Precomputed corridor segments (nm) — illustrative only
ROUTES: dict[tuple[str, str], dict[str, Any]] = {
    ("SGSIN", "NLRTM"): {
        "distance_nm": 8400,
        "typical_days": 28,
        "weather_risk": "medium",
        "seasonal_note": "Winter North Atlantic can add 2–4 days delay risk.",
    },
    ("AEJEA", "NLRTM"): {
        "distance_nm": 6200,
        "typical_days": 22,
        "weather_risk": "medium",
        "seasonal_note": "Red Sea / Suez corridor subject to security advisories.",
    },
    ("CNYTN", "USLAX"): {
        "distance_nm": 5800,
        "typical_days": 18,
        "weather_risk": "low",
        "seasonal_note": "Typhoon season Jul–Oct: reroute risk west of Guam.",
    },
    ("SGSIN", "AEJEA"): {
        "distance_nm": 3200,
        "typical_days": 11,
        "weather_risk": "low",
        "seasonal_note": "Monsoon swell in Bay of Bengal Mar–Apr.",
    },
}

SECURITY_ZONES: dict[str, dict[str, Any]] = {
    "RED_SEA": {
        "level": "elevated",
        "summary": "Heightened security; escort / BMP5 practices advised in corridor.",
        "piracy_index": 0.35,
    },
    "GULF_GUINEA": {
        "level": "high",
        "summary": "Kidnap-for-ransom risk; strict watch and reporting protocols.",
        "piracy_index": 0.62,
    },
    "MALACCA": {
        "level": "moderate",
        "summary": "Dense traffic; petty theft at anchor; VTS cooperation.",
        "piracy_index": 0.22,
    },
    "HORN_AFRICA": {
        "level": "elevated",
        "summary": "Long-range piracy historically; coalition patrols active.",
        "piracy_index": 0.41,
    },
}

ALERTS: list[dict[str, Any]] = [
    {
        "id": "ALT-2025-07",
        "title": "Strait transit advisory (training data)",
        "severity": "medium",
        "corridor": "RED_SEA",
        "body": "Synthetic drill: delay insurance add-on may apply for certain flags.",
    },
    {
        "id": "ALT-2025-08",
        "title": "Fuel sulphur spot checks (EU ETS zone)",
        "severity": "low",
        "corridor": "NWE",
        "body": "Illustrative: ensure VLSFO bunkers match BDN specs in ARA range.",
    },
    {
        "id": "ALT-2025-09",
        "title": "Weather: North Pacific low sequence",
        "severity": "medium",
        "corridor": "PAC_TRANS",
        "body": "Synthetic: ballast voyages may seek southerly great-circle offset.",
    },
]

# $/mt VLSFO-style index by region (synthetic static snapshot)
FUEL_INDEX: dict[str, dict[str, Any]] = {
    "SINGAPORE": {"vlsfo_usd_mt": 612, "trend_7d_pct": -1.2},
    "ROTTERDAM": {"vlsfo_usd_mt": 598, "trend_7d_pct": 0.4},
    "FUJAIRAH": {"vlsfo_usd_mt": 605, "trend_7d_pct": -0.8},
    "USGC": {"vlsfo_usd_mt": 621, "trend_7d_pct": 1.1},
}


def list_ports() -> list[str]:
    return sorted(PORTS.keys())


def normalize_route(origin: str, dest: str) -> tuple[str, str]:
    o, d = origin.upper().strip(), dest.upper().strip()
    if o not in PORTS or d not in PORTS:
        raise ValueError(f"Unknown port code(s). Known: {', '.join(list_ports())}")
    if o == d:
        raise ValueError("Origin and destination must differ.")
    return o, d


def get_route_snapshot(origin: str, dest: str) -> dict[str, Any]:
    """Weather / transit snapshot for a predefined corridor (synthetic)."""
    o, d = normalize_route(origin, dest)
    key = (o, d)
    rev = (d, o)
    if key in ROUTES:
        seg = ROUTES[key]
    elif rev in ROUTES:
        seg = ROUTES[rev]
    else:
        # Fallback: rough synthetic from pseudo great-circle
        dist = abs(PORTS[o]["lat"] - PORTS[d]["lat"]) * 60 + abs(PORTS[o]["lon"] - PORTS[d]["lon"]) * 40
        seg = {
            "distance_nm": int(dist),
            "typical_days": max(8, int(dist / 320)),
            "weather_risk": "medium",
            "seasonal_note": "Interpolated corridor — use for demo only.",
        }
    return {
        "origin": o,
        "destination": d,
        "origin_name": PORTS[o]["name"],
        "dest_name": PORTS[d]["name"],
        "distance_nm": seg["distance_nm"],
        "typical_days": seg["typical_days"],
        "weather_risk": seg["weather_risk"],
        "sea_state_hint": _sea_state_from_risk(seg["weather_risk"]),
        "seasonal_note": seg["seasonal_note"],
        "disclaimer": "Synthetic coursework data — not a weather forecast.",
    }


def _sea_state_from_risk(risk: str) -> str:
    return {"low": "Mostly moderate seas", "medium": "Mixed moderate/rough", "high": "Rough possible"}.get(
        risk, "Variable"
    )


def get_security_advisory(region_code: str) -> dict[str, Any]:
    code = region_code.upper().strip()
    if code not in SECURITY_ZONES:
        known = ", ".join(sorted(SECURITY_ZONES))
        raise ValueError(f"Unknown region. Use one of: {known}")
    z = SECURITY_ZONES[code]
    return {
        "region": code,
        "level": z["level"],
        "summary": z["summary"],
        "piracy_index_0_to_1": z["piracy_index"],
        "disclaimer": "Illustrative risk index — not official UKMTO/MSCHOA guidance.",
    }


def list_security_regions() -> list[str]:
    return sorted(SECURITY_ZONES.keys())


def list_active_alerts() -> list[dict[str, Any]]:
    return [dict(a) for a in ALERTS]


def get_fuel_price_index(ref_region: str) -> dict[str, Any]:
    key = ref_region.upper().strip()
    # Allow loose matching
    alias = {
        "SINGAPORE": "SINGAPORE",
        "SG": "SINGAPORE",
        "ROTTERDAM": "ROTTERDAM",
        "EU": "ROTTERDAM",
        "FUJAIRAH": "FUJAIRAH",
        "ME": "FUJAIRAH",
        "USGC": "USGC",
        "US": "USGC",
    }
    k = alias.get(key, key)
    if k not in FUEL_INDEX:
        raise ValueError(f"Unknown region. Keys: {', '.join(FUEL_INDEX)}")
    row = FUEL_INDEX[k]
    return {
        "region": k,
        "vlsfo_usd_per_mt": row["vlsfo_usd_mt"],
        "trend_7d_pct": row["trend_7d_pct"],
        "disclaimer": "Synthetic static snapshot — not a market quote.",
    }


def estimate_voyage_cost_stub(
    distance_nm: float,
    days: float,
    fuel_region: str = "SINGAPORE",
    daily_opex_usd: float = 12000,
    consumption_mt_per_day: float = 35,
) -> dict[str, Any]:
    """
    Very rough bunker + time cost (synthetic).
    Not for fixture negotiation or accounting.
    """
    if distance_nm <= 0 or days <= 0:
        raise ValueError("distance_nm and days must be positive.")
    fuel_info = get_fuel_price_index(fuel_region)
    price = float(fuel_info["vlsfo_usd_per_mt"])
    fuel_mt = max(0.0, consumption_mt_per_day * days)
    fuel_cost = fuel_mt * price
    opex = daily_opex_usd * days
    total = fuel_cost + opex
    return {
        "inputs": {
            "distance_nm": distance_nm,
            "days": days,
            "fuel_region": fuel_info["region"],
            "daily_opex_usd": daily_opex_usd,
            "consumption_mt_per_day": consumption_mt_per_day,
        },
        "fuel_mt": round(fuel_mt, 1),
        "fuel_cost_usd": round(fuel_cost, 0),
        "time_cost_usd": round(opex, 0),
        "total_estimated_usd": round(total, 0),
        "disclaimer": "Stub calculator for learning — omitting canal fees, port costs, demurrage, carbon schemes.",
    }


def corridor_summary(origin: str, dest: str) -> dict[str, Any]:
    """One-shot: route + suggested security zones to review + fuel ref."""
    snap = get_route_snapshot(origin, dest)
    # Map rough zones by hemisphere / known corridors (demo logic)
    zones: list[str] = []
    o, d = snap["origin"], snap["destination"]
    if "AEJEA" in (o, d) or "NLRTM" in (o, d):
        zones.extend(["RED_SEA", "MALACCA"])
    if "USLAX" in (o, d) or "CNYTN" in (o, d):
        zones.append("MALACCA")
    if "SGSIN" in (o, d):
        zones.append("MALACCA")
    zones = list(dict.fromkeys(zones))
    advisories = [get_security_advisory(z) for z in zones]
    fuel = get_fuel_price_index("SINGAPORE")
    return {
        "route": snap,
        "security_zones_to_review": advisories,
        "reference_fuel": fuel,
        "disclaimer": "Aggregated synthetic briefing — verify with official sources.",
    }
