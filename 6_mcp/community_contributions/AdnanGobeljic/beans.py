from __future__ import annotations


ORIGINS = {
    "ETH-YRG": {
        "name": "Yirgacheffe",
        "country": "Ethiopia",
        "altitude_m": 1900,
        "process": "washed",
        "harvest": "Oct-Jan",
    },
    "COL-HUI": {
        "name": "Huila",
        "country": "Colombia",
        "altitude_m": 1650,
        "process": "washed",
        "harvest": "Sep-Dec",
    },
    "BRA-SMO": {
        "name": "Santos Mogiana",
        "country": "Brazil",
        "altitude_m": 1100,
        "process": "natural",
        "harvest": "May-Sep",
    },
    "KEN-AA": {
        "name": "Kenya AA",
        "country": "Kenya",
        "altitude_m": 1700,
        "process": "washed",
        "harvest": "Oct-Dec",
    },
    "GTM-ANT": {
        "name": "Antigua",
        "country": "Guatemala",
        "altitude_m": 1500,
        "process": "washed",
        "harvest": "Jan-Mar",
    },
    "IDN-MAN": {
        "name": "Mandheling",
        "country": "Indonesia",
        "altitude_m": 1300,
        "process": "wet-hulled",
        "harvest": "Jun-Sep",
    },
}

ROAST_LEVELS = {
    "light": {"temp_c": 205, "time_min": 9, "first_crack": True, "second_crack": False},
    "medium": {"temp_c": 215, "time_min": 11, "first_crack": True, "second_crack": False},
    "medium-dark": {"temp_c": 225, "time_min": 13, "first_crack": True, "second_crack": True},
    "dark": {"temp_c": 235, "time_min": 14, "first_crack": True, "second_crack": True},
}

FLAVOR_MAP = {
    ("ETH-YRG", "light"): ["blueberry", "jasmine", "citrus"],
    ("ETH-YRG", "medium"): ["stone fruit", "honey", "tea-like"],
    ("COL-HUI", "light"): ["caramel", "red apple", "bright"],
    ("COL-HUI", "medium"): ["chocolate", "nutty", "balanced"],
    ("BRA-SMO", "medium"): ["chocolate", "peanut", "low acid"],
    ("BRA-SMO", "dark"): ["smoky", "bittersweet", "full body"],
    ("KEN-AA", "light"): ["blackcurrant", "grapefruit", "winey"],
    ("KEN-AA", "medium"): ["berry", "brown sugar", "juicy"],
    ("GTM-ANT", "medium"): ["cocoa", "spice", "smooth"],
    ("GTM-ANT", "medium-dark"): ["dark chocolate", "cedar", "rich"],
    ("IDN-MAN", "medium-dark"): ["earthy", "tobacco", "syrupy"],
    ("IDN-MAN", "dark"): ["dark chocolate", "smoky", "heavy"],
}

BREW_METHODS = {
    "pourover": {"ratio": "1:16", "grind": "medium-fine", "water_temp_c": 93, "time_min": 3.5},
    "french_press": {"ratio": "1:15", "grind": "coarse", "water_temp_c": 96, "time_min": 4},
    "espresso": {"ratio": "1:2", "grind": "fine", "water_temp_c": 93, "time_min": 0.5},
    "aeropress": {"ratio": "1:12", "grind": "medium", "water_temp_c": 85, "time_min": 2},
    "cold_brew": {"ratio": "1:8", "grind": "coarse", "water_temp_c": 4, "time_min": 720},
}

PRICES = {
    "ETH-YRG": 8.50,
    "COL-HUI": 6.20,
    "BRA-SMO": 4.10,
    "KEN-AA": 9.00,
    "GTM-ANT": 5.80,
    "IDN-MAN": 5.50,
}

SHRINK = 0.15 


def list_beans():
    return sorted(ORIGINS.keys())


def get_bean(code):
    c = code.upper().strip()
    if c not in ORIGINS:
        raise ValueError(f"no bean '{c}'. try: {', '.join(list_beans())}")
    info = dict(ORIGINS[c])
    info["code"] = c
    return info


def list_roast_levels():
    return list(ROAST_LEVELS.keys())


def get_roast_profile(level):
    lv = level.lower().strip()
    if lv not in ROAST_LEVELS:
        raise ValueError(f"unknown roast level. pick from: {', '.join(ROAST_LEVELS)}")
    return dict(ROAST_LEVELS[lv])


def flavor_notes(bean_code, roast_level):
    c = bean_code.upper().strip()
    lv = roast_level.lower().strip()
    key = (c, lv)

    if key in FLAVOR_MAP:
        return {"bean": c, "roast": lv, "notes": FLAVOR_MAP[key]}

    if lv == "light":
        return {"bean": c, "roast": lv, "notes": ["bright", "floral", "acidic"]}
    if lv in ("dark", "medium-dark"):
        return {"bean": c, "roast": lv, "notes": ["bitter", "smoky", "full body"]}


    return {"bean": c, "roast": lv, "notes": ["balanced", "mild", "clean"]}


def brew_recipe(method):
    m = method.lower().strip().replace(" ", "_").replace("-", "_")

    if m not in BREW_METHODS:
        raise ValueError(f"unknown method. pick from: {', '.join(BREW_METHODS)}")
    rec = dict(BREW_METHODS[m])
    rec["method"] = m


    return rec


def batch_cost(bean_code, green_kg):
    c = bean_code.upper().strip()

    if c not in PRICES:
        raise ValueError(f"no price for '{c}'")
    if green_kg <= 0:
        raise ValueError("weight has to be positive")


    green_cost = PRICES[c] * green_kg
    roasted_kg = green_kg * (1 - SHRINK)

    return {
        "bean": c,
        "green_kg": green_kg,
        "green_cost_usd": round(green_cost, 2),
        "roasted_kg": round(roasted_kg, 2),
        "cost_per_roasted_kg": round(green_cost / roasted_kg, 2),
    }


def recommend(bean_code, roast_level, method):
    """Bean info + roast profile + flavor notes + brew params in one shot."""


    bean = get_bean(bean_code)
    notes = flavor_notes(bean_code, roast_level)
    profile = get_roast_profile(roast_level)
    brew = brew_recipe(method)

    return {
        "bean": bean,
        "roast_profile": profile,
        "expected_flavors": notes["notes"],
        "brew_params": brew,
    }
