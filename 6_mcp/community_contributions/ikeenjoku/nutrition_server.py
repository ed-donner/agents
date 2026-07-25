import json

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nutrition_server")

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
OFF_SEARCH = "https://world.openfoodfacts.net/cgi/search.pl"


async def _lookup_nutrition(food_item: str) -> dict | None:
    """look up nutrition for a food item via Open Food Facts.
    Returns a dict with per-100g values, or None on failure."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            OFF_SEARCH,
            params={
                "search_terms": food_item,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
                "fields": "product_name,nutriments,brands",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    products = data.get("products") or []
    for p in products:
        n = p.get("nutriments")
        if not n:
            continue
        return {
            "food": p.get("product_name") or food_item,
            "brand": p.get("brands") or "",
            "per_100g": {
                "calories_kcal": n.get("energy-kcal_100g", 0),
                "protein_g": n.get("proteins_100g", 0),
                "carbs_g": n.get("carbohydrates_100g", 0),
                "fat_g": n.get("fat_100g", 0),
                "fiber_g": n.get("fiber_100g", 0),
            },
        }
    return None


def _parse_ingredients(meal: dict) -> list[str]:
    """Extract non-empty ingredient+measure pairs from a TheMealDB meal."""
    ingredients = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            ingredients.append(f"{measure} {ing}".strip())
    return ingredients


@mcp.tool()
async def search_recipes(query: str, dietary_filter: str = "") -> str:
    """Search for recipes by keyword, optionally filtered by category"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{MEALDB_BASE}/search.php", params={"s": query})
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return f"Recipe search failed: {e}"

    meals = data.get("meals") or []
    if not meals:
        return "No recipes found. Try a different keyword."

    if dietary_filter:
        filt = dietary_filter.lower()
        meals = [m for m in meals if filt in (m.get("strCategory") or "").lower()]

    results = []
    for m in meals[:8]:
        ingredients = _parse_ingredients(m)
        results.append({
            "name": m.get("strMeal"),
            "category": m.get("strCategory"),
            "cuisine": m.get("strArea"),
            "ingredients": ingredients[:10],
            "instructions_preview": (m.get("strInstructions") or "")[:200] + "...",
        })

    if not results:
        return f"No recipes matched the filter '{dietary_filter}'. Try without a filter."

    return json.dumps(results, indent=2)


@mcp.tool()
async def get_nutrition_info(food_item: str) -> str:
    """Look up nutritional information (calories, protein, carbs, fat) for a food item"""
    try:
        result = await _lookup_nutrition(food_item)
    except httpx.HTTPError as e:
        return f"Nutrition lookup failed: {e}"

    if result is None:
        return f"No nutrition data found for '{food_item}'. Try a more specific name."

    return json.dumps(result, indent=2)


@mcp.tool()
async def calculate_daily_totals(meals: str) -> str:
    """Sum up nutritional values for a list of food items."""
    try:
        items = json.loads(meals)
    except json.JSONDecodeError:
        return (
            "Invalid JSON. Expected format: "
            '[{"item": "food name", "servings": 1.0}, ...]'
        )

    totals = {"calories_kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}
    breakdown = []

    for entry in items:
        name = entry.get("item", "unknown")
        servings = float(entry.get("servings", 1))

        try:
            info = await _lookup_nutrition(name)
        except Exception:
            breakdown.append({"item": name, "error": "lookup failed"})
            continue

        if info is None:
            breakdown.append({"item": name, "error": "not found"})
            continue

        per_100g = info["per_100g"]
        item_totals = {}
        for key in totals:
            val = per_100g.get(key, 0) * servings
            totals[key] += val
            item_totals[key] = round(val, 1)

        breakdown.append({
            "item": name,
            "servings_100g": servings,
            "nutrients": item_totals,
        })

    return json.dumps(
        {"items": breakdown, "daily_totals": {k: round(v, 1) for k, v in totals.items()}},
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
