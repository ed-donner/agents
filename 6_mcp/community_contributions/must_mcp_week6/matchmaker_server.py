import json
import logging
import random
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Configure robust logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matchmaker_server")

mcp = FastMCP('matchmaker_server')

@mcp.tool()
def get_cost_of_living(city: str) -> str:
    """Get the standard cost of living index and average rent for a given city.
    
    Args:
        city: The name of the city.
    """
    try:
        base_rent = 1200
        city_lower = city.lower().strip()
        
        if city_lower in ['new york', 'san francisco', 'seattle']:
            base_rent += 1500
        elif city_lower in ['austin', 'denver', 'miami']:
            base_rent += 800
            
        data: Dict[str, Any] = {
            "city": city,
            "average_rent_usd": base_rent + random.randint(-200, 200),
            "groceries_monthly_usd": random.randint(300, 600),
            "transit_monthly_usd": random.randint(50, 150)
        }
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error calculating cost of living for {city}: {e}")
        return json.dumps({"error": "Unable to fetch cost of living data."})

@mcp.tool()
def find_apartments(city: str, budget: int) -> str:
    """Find available apartment listings in a city under a specific budget.
    
    Args:
        city: The name of the city.
        budget: Maximum monthly rent budget in USD.
    """
    try:
        names = ["The Vue", "City Center Lofts", "Sunset Apartments", "Riverside Park", "Greenwood Hub"]
        results = []
        
        # Ensure budget is an int and reasonable
        budget = int(budget)
        
        for _ in range(3):
            price = random.randint(800, budget) if budget >= 800 else budget
            results.append({
                "name": random.choice(names),
                "price_usd": price,
                "bedrooms": random.choice([1, 2, 3]),
                "amenities": random.sample(["Gym", "Pool", "In-unit Washer", "Doorman"], k=2)
            })
            
        return json.dumps({"apartments": results})
    except ValueError:
        logger.warning(f"Invalid budget format provided: {budget}")
        return json.dumps({"error": "Budget must be a valid number."})
    except Exception as e:
        logger.error(f"Error fetching apartments: {e}")
        return json.dumps({"error": "Unable to fetch apartments."})

@mcp.tool()
def get_neighborhood_vibe(city: str) -> str:
    """Get the general cultural or lifestyle vibe of a city.
    
    Args:
        city: The name of the city.
    """
    try:
        vibes = {
            "austin": "Very vibrant, known for live music scenes, tech startups, and great BBQ. Has a growing but distinct artistic vibe.",
            "seattle": "Rainy and cozy. Incredible coffee culture, very tech-heavy, surrounded by gorgeous mountains and nature.",
            "new york": "Fast-paced and bustling. You can find anything 24/7. Diverse neighborhoods with intense energy and high walkability.",
        }
        
        city_lower = city.lower().strip()
        description = vibes.get(city_lower, "A classic metropolitan area with a mix of residential quiet zones and a busy downtown core.")
        return json.dumps({"city": city, "vibe": description})
    except Exception as e:
        logger.error(f"Error fetching vibe for {city}: {e}")
        return json.dumps({"error": "Unable to fetch neighborhood data."})

if __name__ == "__main__":
    logger.info("Starting Matchmaker MCP Server on stdio transport...")
    mcp.run(transport='stdio')
