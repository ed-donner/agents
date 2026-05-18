import json
import sqlite3
import httpx
from mcp.server.fastmcp import FastMCP
from datetime import date

mcp = FastMCP("meal_planner")

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"

DB_PATH = "meal_plans.db"


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            meal_id TEXT,
            notes TEXT DEFAULT ''
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_date TEXT NOT NULL,
            ingredient TEXT NOT NULL,
            measure TEXT DEFAULT '',
            checked INTEGER DEFAULT 0
        )"""
    )
    conn.commit()
    conn.close()


_init_db()


def _parse_ingredients(meal: dict) -> list[dict]:
    ingredients = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        meas = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            ingredients.append({"ingredient": ing, "measure": meas})
    return ingredients


# --------------- Recipe Search Tools ---------------


@mcp.tool()
async def search_recipes(query: str) -> str:
    """Search for recipes by name keyword. Returns a list of matching meals with their IDs.

    Args:
        query: A keyword to search for (e.g. 'chicken', 'pasta', 'soup')
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/search.php", params={"s": query})
        data = resp.json()
    meals = data.get("meals") or []
    results = [
        {"id": m["idMeal"], "name": m["strMeal"], "category": m["strCategory"], "cuisine": m["strArea"]}
        for m in meals
    ]
    return json.dumps(results[:10], indent=2) if results else "No recipes found for that query."


@mcp.tool()
async def get_recipe_details(meal_id: str) -> str:
    """Get full details of a recipe including ingredients and instructions.

    Args:
        meal_id: The TheMealDB meal ID
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/lookup.php", params={"i": meal_id})
        data = resp.json()
    meals = data.get("meals") or []
    if not meals:
        return "Recipe not found."
    m = meals[0]
    ingredients = _parse_ingredients(m)
    return json.dumps(
        {
            "name": m["strMeal"],
            "category": m["strCategory"],
            "cuisine": m["strArea"],
            "instructions": m["strInstructions"],
            "ingredients": ingredients,
            "image": m.get("strMealThumb", ""),
            "youtube": m.get("strYoutube", ""),
        },
        indent=2,
    )


@mcp.tool()
async def browse_by_category(category: str) -> str:
    """Browse recipes by category (e.g. Seafood, Dessert, Vegetarian, Beef, Chicken, Pasta, Starter).

    Args:
        category: The meal category name
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/filter.php", params={"c": category})
        data = resp.json()
    meals = data.get("meals") or []
    results = [{"id": m["idMeal"], "name": m["strMeal"]} for m in meals]
    return json.dumps(results[:15], indent=2) if results else f"No meals found in category '{category}'."


@mcp.tool()
async def browse_by_cuisine(cuisine: str) -> str:
    """Browse recipes by cuisine/area (e.g. Italian, Japanese, Mexican, Indian, British, American).

    Args:
        cuisine: The cuisine or area name
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/filter.php", params={"a": cuisine})
        data = resp.json()
    meals = data.get("meals") or []
    results = [{"id": m["idMeal"], "name": m["strMeal"]} for m in meals]
    return json.dumps(results[:15], indent=2) if results else f"No meals found for cuisine '{cuisine}'."


@mcp.tool()
async def random_recipe() -> str:
    """Get a random recipe for inspiration."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/random.php")
        data = resp.json()
    m = data["meals"][0]
    ingredients = _parse_ingredients(m)
    return json.dumps(
        {
            "name": m["strMeal"],
            "id": m["idMeal"],
            "category": m["strCategory"],
            "cuisine": m["strArea"],
            "ingredients": ingredients,
            "instructions": m["strInstructions"][:300] + "...",
        },
        indent=2,
    )


@mcp.tool()
async def list_categories() -> str:
    """List all available meal categories."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/categories.php")
        data = resp.json()
    cats = data.get("categories") or []
    return json.dumps(
        [{"name": c["strCategory"], "description": c["strCategoryDescription"][:80]} for c in cats],
        indent=2,
    )


@mcp.tool()
async def filter_by_ingredient(ingredient: str) -> str:
    """Find recipes that use a specific ingredient.

    Args:
        ingredient: The ingredient to filter by (e.g. 'chicken_breast', 'rice', 'salmon')
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MEALDB_BASE}/filter.php", params={"i": ingredient})
        data = resp.json()
    meals = data.get("meals") or []
    results = [{"id": m["idMeal"], "name": m["strMeal"]} for m in meals]
    return json.dumps(results[:15], indent=2) if results else f"No recipes found with ingredient '{ingredient}'."


# --------------- Meal Plan Tools ---------------


@mcp.tool()
async def add_to_meal_plan(plan_date: str, meal_type: str, meal_name: str, meal_id: str = "", notes: str = "") -> str:
    """Add a meal to the meal plan for a specific date and meal slot.

    Args:
        plan_date: The date in YYYY-MM-DD format
        meal_type: One of 'breakfast', 'lunch', 'dinner', or 'snack'
        meal_name: The name of the meal
        meal_id: Optional TheMealDB meal ID for linking back to the recipe
        notes: Optional notes (dietary swaps, serving size, etc.)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO meal_plans (plan_date, meal_type, meal_name, meal_id, notes) VALUES (?, ?, ?, ?, ?)",
        (plan_date, meal_type.lower(), meal_name, meal_id, notes),
    )
    conn.commit()
    conn.close()
    return f"Added '{meal_name}' as {meal_type} on {plan_date}."


@mcp.tool()
async def view_meal_plan(start_date: str, end_date: str) -> str:
    """View the meal plan for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT plan_date, meal_type, meal_name, notes FROM meal_plans WHERE plan_date BETWEEN ? AND ? ORDER BY plan_date, meal_type",
        (start_date, end_date),
    ).fetchall()
    conn.close()
    if not rows:
        return f"No meals planned between {start_date} and {end_date}."
    plan = {}
    for row in rows:
        day = row[0]
        if day not in plan:
            plan[day] = []
        plan[day].append({"meal_type": row[1], "meal": row[2], "notes": row[3]})
    return json.dumps(plan, indent=2)


@mcp.tool()
async def remove_from_meal_plan(plan_date: str, meal_type: str) -> str:
    """Remove a meal from the plan.

    Args:
        plan_date: The date in YYYY-MM-DD format
        meal_type: The meal slot to clear (breakfast, lunch, dinner, snack)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM meal_plans WHERE plan_date = ? AND meal_type = ?",
        (plan_date, meal_type.lower()),
    )
    conn.commit()
    conn.close()
    return f"Removed {meal_type} on {plan_date}."


# --------------- Shopping List Tools ---------------


@mcp.tool()
async def generate_shopping_list(start_date: str, end_date: str) -> str:
    """Generate a consolidated shopping list from the meal plan for a date range.
    Looks up ingredients for each planned meal that has a meal_id.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT meal_id, meal_name FROM meal_plans WHERE plan_date BETWEEN ? AND ? AND meal_id != ''",
        (start_date, end_date),
    ).fetchall()
    conn.close()

    if not rows:
        return "No meals with linked recipes found in that date range."

    all_ingredients: dict[str, str] = {}
    async with httpx.AsyncClient() as client:
        for meal_id, meal_name in rows:
            resp = await client.get(f"{MEALDB_BASE}/lookup.php", params={"i": meal_id})
            data = resp.json()
            meals = data.get("meals") or []
            if meals:
                for item in _parse_ingredients(meals[0]):
                    key = item["ingredient"].lower()
                    if key in all_ingredients:
                        all_ingredients[key] += f" + {item['measure']}"
                    else:
                        all_ingredients[key] = item["measure"]

    # Persist to shopping_items table
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM shopping_items WHERE plan_date BETWEEN ? AND ?", (start_date, end_date))
    for ing, meas in all_ingredients.items():
        conn.execute(
            "INSERT INTO shopping_items (plan_date, ingredient, measure) VALUES (?, ?, ?)",
            (start_date, ing, meas),
        )
    conn.commit()
    conn.close()

    shopping = [{"ingredient": k, "measure": v} for k, v in sorted(all_ingredients.items())]
    return json.dumps(shopping, indent=2)


@mcp.resource("mealplan://week/{start_date}")
async def read_week_plan(start_date: str) -> str:
    """Read the meal plan for the week starting on start_date."""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(days=6)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT plan_date, meal_type, meal_name, notes FROM meal_plans WHERE plan_date BETWEEN ? AND ? ORDER BY plan_date, meal_type",
        (start_date, end.strftime("%Y-%m-%d")),
    ).fetchall()
    conn.close()
    if not rows:
        return "No meals planned for this week."
    plan = {}
    for row in rows:
        day = row[0]
        if day not in plan:
            plan[day] = []
        plan[day].append({"meal_type": row[1], "meal": row[2], "notes": row[3]})
    return json.dumps(plan, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
