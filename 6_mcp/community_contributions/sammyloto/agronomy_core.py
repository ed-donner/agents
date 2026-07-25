"""
Synthetic agronomy reference data and calculators for coursework demos.

Not for real farm management, regulatory compliance, or pesticide/fertilizer decisions.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any

# --- Agro-ecological zones (illustrative codes) --------------------------------

ZONES: dict[str, dict[str, Any]] = {
    "HRV-HIGH": {
        "label": "Highland tropics — bimodal rains",
        "approx_elevation_m": (1400, 2200),
        "frost_risk": "low",
        "rainy_seasons": ["Mar-May", "Sep-Nov"],
        "typical_frost_free_months": list(range(1, 13)),
    },
    "SAV-MID": {
        "label": "Savanna — single wet season",
        "approx_elevation_m": (800, 1400),
        "frost_risk": "none",
        "rainy_seasons": ["Apr-Oct"],
        "typical_frost_free_months": list(range(1, 13)),
    },
    "MED-COAST": {
        "label": "Mediterranean coastal — winter rain",
        "approx_elevation_m": (0, 600),
        "frost_risk": "light_winter",
        "rainy_seasons": ["Nov-Mar"],
        "typical_frost_free_months": [4, 5, 6, 7, 8, 9, 10, 11],
    },
}

# Monthly typical Tmax/Tmin (°C) by zone — synthetic seasonal curves
MONTHLY_TEMPS: dict[str, list[tuple[float, float]]] = {
    "HRV-HIGH": [
        (24, 11),
        (25, 12),
        (26, 13),
        (25, 13),
        (24, 12),
        (23, 11),
        (22, 10),
        (23, 10),
        (24, 11),
        (25, 12),
        (25, 12),
        (24, 11),
    ],
    "SAV-MID": [
        (30, 14),
        (32, 16),
        (33, 17),
        (32, 17),
        (30, 16),
        (28, 14),
        (27, 13),
        (28, 14),
        (30, 15),
        (31, 16),
        (31, 16),
        (30, 15),
    ],
    "MED-COAST": [
        (14, 6),
        (15, 7),
        (17, 8),
        (20, 10),
        (24, 13),
        (28, 17),
        (31, 20),
        (31, 20),
        (28, 18),
        (23, 14),
        (18, 10),
        (15, 8),
    ],
}

CROPS: dict[str, dict[str, Any]] = {
    "maize": {
        "name": "Maize (grain)",
        "tbase_c": 10.0,
        "gdd_to_maturity_typical": 1400,
        "water_mm_season_typical": 450,
        "family": "Poaceae",
    },
    "common_bean": {
        "name": "Common bean",
        "tbase_c": 10.0,
        "gdd_to_maturity_typical": 1200,
        "water_mm_season_typical": 350,
        "family": "Fabaceae",
    },
    "wheat": {
        "name": "Winter wheat",
        "tbase_c": 0.0,
        "gdd_to_maturity_typical": 2200,
        "water_mm_season_typical": 400,
        "family": "Poaceae",
    },
    "tomato": {
        "name": "Tomato",
        "tbase_c": 10.0,
        "gdd_to_maturity_typical": 900,
        "water_mm_season_typical": 400,
        "family": "Solanaceae",
    },
    "coffee": {
        "name": "Arabica coffee",
        "tbase_c": 10.0,
        "gdd_to_maturity_typical": 3000,
        "water_mm_season_typical": 1200,
        "family": "Rubiaceae",
    },
    "cassava": {
        "name": "Cassava",
        "tbase_c": 12.0,
        "gdd_to_maturity_typical": 2500,
        "water_mm_season_typical": 600,
        "family": "Euphorbiaceae",
    },
}

SOILS: dict[str, dict[str, Any]] = {
    "clay_loam": {
        "label": "Clay loam",
        "available_water_mm_per_m": 140,
        "infiltration": "moderate",
    },
    "sandy_loam": {
        "label": "Sandy loam",
        "available_water_mm_per_m": 100,
        "infiltration": "fast",
    },
    "silt_loam": {
        "label": "Silt loam",
        "available_water_mm_per_m": 170,
        "infiltration": "moderate_slow",
    },
}

# Legume → following crop synergy (synthetic scores 0–1)
ROTATION_SCORE: dict[tuple[str, str], float] = {
    ("common_bean", "maize"): 0.92,
    ("maize", "common_bean"): 0.88,
    ("wheat", "common_bean"): 0.85,
    ("cassava", "common_bean"): 0.7,
    ("tomato", "common_bean"): 0.65,
    ("tomato", "maize"): 0.55,
    ("maize", "maize"): 0.45,
}


def list_zones() -> list[str]:
    return sorted(ZONES.keys())


def list_crops() -> list[str]:
    return sorted(CROPS.keys())


def list_soil_textures() -> list[str]:
    return sorted(SOILS.keys())


def _month_index(d: date) -> int:
    return d.month - 1


def daily_gdd(tmax: float, tmin: float, tbase: float) -> float:
    """Single-day GDD using mean temperature vs base (simple agrometeorology stub)."""
    tmean = (tmax + tmin) / 2.0
    return max(0.0, tmean - tbase)


def accumulate_gdd(zone_code: str, crop_code: str, start: date, end: date) -> dict[str, Any]:
    if zone_code not in ZONES:
        raise ValueError(f"Unknown zone {zone_code!r}. Known: {list_zones()}")
    if crop_code not in CROPS:
        raise ValueError(f"Unknown crop {crop_code!r}. Known: {list_crops()}")
    tbase = CROPS[crop_code]["tbase_c"]
    temps = MONTHLY_TEMPS[zone_code]
    total = 0.0
    day = start
    while day <= end:
        tmax, tmin = temps[_month_index(day)]
        total += daily_gdd(tmax, tmin, tbase)
        day = date.fromordinal(day.toordinal() + 1)
    return {
        "zone": zone_code,
        "crop": crop_code,
        "tbase_c": tbase,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "gdd_sum": round(total, 1),
        "gdd_target_typical": CROPS[crop_code]["gdd_to_maturity_typical"],
        "fraction_of_typical_maturity_gdd": round(
            total / max(1, CROPS[crop_code]["gdd_to_maturity_typical"]), 3
        ),
    }


def suggest_planting_window(crop_code: str, zone_code: str) -> dict[str, Any]:
    if zone_code not in ZONES:
        raise ValueError(f"Unknown zone {zone_code!r}. Known: {list_zones()}")
    if crop_code not in CROPS:
        raise ValueError(f"Unknown crop {crop_code!r}. Known: {list_crops()}")
    target = CROPS[crop_code]["gdd_to_maturity_typical"]
    best_start_month = 1
    best_score = -1.0
    y = date.today().year
    for start_m in range(1, 13):
        start = date(y, start_m, 1)
        end = date.fromordinal(start.toordinal() + 120)
        gdd = accumulate_gdd(zone_code, crop_code, start, end)["gdd_sum"]
        # Prefer ~first third of total GDD in the establishment window (illustrative).
        ideal_segment = target * 0.38
        score = 1.0 / (1.0 + abs(gdd - ideal_segment))
        if gdd >= target * 0.2 and score > best_score:
            best_score = score
            best_start_month = start_m
    rainy = ZONES[zone_code]["rainy_seasons"]
    return {
        "crop": crop_code,
        "zone": zone_code,
        "suggested_primary_planting_month": best_start_month,
        "rainy_seasons_in_zone": rainy,
        "note": "Synthetic heuristic: align sowing with reliable soil moisture; validate locally.",
    }


def soil_water_status(
    soil_texture: str,
    root_depth_m: float,
    last_rain_mm: float,
    days_since_rain: int,
    et0_mm_per_day: float,
) -> dict[str, Any]:
    if soil_texture not in SOILS:
        raise ValueError(f"Unknown soil {soil_texture!r}. Known: {list_soil_textures()}")
    aw = SOILS[soil_texture]["available_water_mm_per_m"] * max(0.2, min(root_depth_m, 1.5))
    depletion = days_since_rain * et0_mm_per_day * 0.6
    effective = max(0.0, last_rain_mm + aw * 0.5 - depletion)
    ratio = min(1.0, effective / max(1.0, aw))
    stress = "low" if ratio > 0.55 else "moderate" if ratio > 0.3 else "high"
    return {
        "soil_texture": soil_texture,
        "approx_available_water_capacity_mm": round(aw, 1),
        "estimated_root_zone_status_ratio": round(ratio, 3),
        "water_stress_band": stress,
        "disclaimer": "Illustrative water balance stub — use field probes and local ET models in practice.",
    }


def rotation_advice(previous_crop: str, next_crop: str) -> dict[str, Any]:
    if previous_crop not in CROPS or next_crop not in CROPS:
        raise ValueError("Unknown crop code(s).")
    key = (previous_crop, next_crop)
    rev = (next_crop, previous_crop)
    score = ROTATION_SCORE.get(key, ROTATION_SCORE.get(rev, 0.72))
    if CROPS[previous_crop]["family"] == CROPS[next_crop]["family"]:
        score *= 0.75
    return {
        "previous_crop": previous_crop,
        "next_crop": next_crop,
        "compatibility_score": round(score, 2),
        "families": [CROPS[previous_crop]["family"], CROPS[next_crop]["family"]],
        "hint": "Higher score = better diversification / disease pressure break (synthetic).",
    }


def pest_pressure_stub(
    week_of_year: int,
    zone_code: str,
    crop_code: str,
) -> dict[str, Any]:
    if zone_code not in ZONES:
        raise ValueError(f"Unknown zone {zone_code!r}.")
    if crop_code not in CROPS:
        raise ValueError(f"Unknown crop {crop_code!r}.")
    phase = (week_of_year % 52) / 52.0 * 2 * math.pi
    base = 0.35 + 0.25 * math.sin(phase)
    if crop_code in ("tomato", "common_bean"):
        base += 0.1
    band = "low" if base < 0.35 else "moderate" if base < 0.55 else "elevated"
    return {
        "week_of_year": week_of_year,
        "zone": zone_code,
        "crop": crop_code,
        "synthetic_pressure_index": round(base, 3),
        "risk_band": band,
        "note": "Training data only — scout fields and use extension thresholds.",
    }


def nutrient_outline_stub(soil_ph: float, organic_matter_pct: float, crop_code: str) -> dict[str, Any]:
    if crop_code not in CROPS:
        raise ValueError(f"Unknown crop {crop_code!r}.")
    n_band = "medium" if 6.0 <= soil_ph <= 7.0 else "adjust_plan"
    om = "high" if organic_matter_pct >= 3.0 else "low"
    return {
        "crop": crop_code,
        "soil_ph": soil_ph,
        "organic_matter_pct": organic_matter_pct,
        "ph_comment": n_band,
        "om_comment": om,
        "illustrative_npk_kg_ha": {"N": 80, "P2O5": 40, "K2O": 40},
        "disclaimer": "Placeholder ranges — soil tests and local recommendations required.",
    }


def field_brief(
    zone_code: str,
    soil_texture: str,
    crop_code: str,
    area_ha: float,
) -> dict[str, Any]:
    if area_ha <= 0:
        raise ValueError("area_ha must be positive.")
    w = suggest_planting_window(crop_code, zone_code)
    sw = soil_water_status(soil_texture, root_depth_m=0.8, last_rain_mm=40, days_since_rain=5, et0_mm_per_day=4.5)
    water_need = CROPS[crop_code]["water_mm_season_typical"] * area_ha
    return {
        "zone": ZONES[zone_code]["label"],
        "soil": SOILS[soil_texture]["label"],
        "crop": CROPS[crop_code]["name"],
        "area_ha": area_ha,
        "planting_hint_month": w["suggested_primary_planting_month"],
        "seasonal_water_demand_mm_times_ha": round(water_need, 0),
        "soil_water_snapshot": sw,
        "summary": "Synthetic briefing for agent demos — confirm all numbers with local agronomists.",
    }
