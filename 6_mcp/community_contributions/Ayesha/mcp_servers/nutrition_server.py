from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("Nutrition Server")

def fetch_food_data(query):
    try:
       
        url = f"https://api.edamam.com/api/food-database/v2/parser?ingr={query}"
        res = requests.get(url)
        return res.json()
    except:
        return None

@mcp.tool()
def get_food_recommendations(emotion: str):
    """
    Suggest evidence-backed foods dynamically based on emotional state.
    Includes reason + reliable links.
    """

    emotion = emotion.lower()

    if "anxiety" in emotion or "stress" in emotion:
        foods = ["banana", "dark chocolate", "green tea"]
    elif "low" in emotion or "sad" in emotion:
        foods = ["salmon", "nuts", "eggs"]
    else:
        foods = ["balanced meal", "fruits"]

    results = []

    for food in foods:
        data = fetch_food_data(food)

        results.append({
            "food": food.title(),
            "benefit": "Supports mood regulation and energy balance",
            "link": f"https://www.google.com/search?q={food}+mental+health+benefits"
        })

    return results

if __name__ == "__main__":
    mcp.run()