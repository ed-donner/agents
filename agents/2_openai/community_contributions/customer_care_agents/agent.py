from google.adk.agents import Agent
import pandas as pd
from google.adk.agents.sequential_agent import SequentialAgent
from pydantic import BaseModel, Field
import json
import random

# --- Data Source ---
# Enhance product names to be more unique using a combination of adjectives, brand, and scent keywords
brands = ["Dior", "Chanel", "Creed", "Tom Ford", "YSL", "Gucci", "Versace", "Armani", "Calvin Klein", "Burberry"]
concentrations = ["Eau de Toilette", "Eau de Parfum", "Parfum", "Cologne"]
genders = ["Men", "Women", "Unisex"]
availability_status = ["In Stock", "Limited Stock", "Out of Stock"]
fragrance_families = ["Woody", "Floral", "Oriental", "Fresh", "Fruity", "Citrus", "Spicy"]
seasons = ["Summer", "Winter", "Spring", "Fall"]
launch_years = list(range(2000, 2024))
adjectives = ["Mystic", "Velvet", "Golden", "Noir", "Crystal", "Amber", "Silken", "Wild", "Intense", "Fresh"]
scent_keywords = ["Whisper", "Flame", "Dream", "Aura", "Pulse", "Echo", "Bloom", "Rush", "Mist", "Twilight"]

# Generate unique perfume data with better product names
def generate_unique_perfume_data(n=30):
    used_names = set()
    products = []

    while len(products) < n:
        brand = random.choice(brands)
        name = f"{random.choice(adjectives)} {random.choice(scent_keywords)} by {brand}"
        if name in used_names:
            continue
        used_names.add(name)
        product = {
            "Product Name": name,
            "Brand": brand,
            "Top Notes": ", ".join(random.sample(["Bergamot", "Lemon", "Mandarin", "Apple", "Pear"], 2)),
            "Heart Notes": ", ".join(random.sample(["Jasmine", "Rose", "Lavender", "Cinnamon", "Cardamom"], 2)),
            "Base Notes": ", ".join(random.sample(["Musk", "Amber", "Cedarwood", "Patchouli", "Vanilla"], 2)),
            "Concentration": random.choice(concentrations),
            "Gender": random.choice(genders),
            "Price (USD)": round(random.uniform(50, 400), 2),
            "Availability": random.choice(availability_status),
            "Fragrance Family": random.choice(fragrance_families),
            "Best Season": random.choice(seasons),
            "Launch Year": random.choice(launch_years),
            "Rating (out of 5)": round(random.uniform(3.0, 5.0), 1)
        }
        products.append(product)
    return products

# Create the updated DataFrame
df = pd.DataFrame(generate_unique_perfume_data(30))

# Query Refiner Agent
query_refiner_agent = Agent(
    name="query_refiner_agent_v1",
    model="gemini-2.0-flash-exp",
    description="Refines the query to be more specific and accurate",
    instruction=(
        "You are a helpful assistant that can refine queries to be more specific and accurate."
        "If user asks for best seller or for random suggestions, search for perfumes with maximum rating."
        "You receive a query and generate a refined query in plain english that another agent will use to generate a pandas expression."
        "The query should be concise and to the point, and should not include any instructions or explanations."
    )
)

# Output Schema of query_generator_agent using pydantic, it should be a valid pandas expression
class QueryGeneratorOutput(BaseModel):
    query: str = Field(description="A valid pandas expression that can be used to query the data.")

# a function that takes a pandas expression and executes it and returns the result, if result is an error, return the error message
def execute_query(query: str):
    try:
        result = eval(query, {'df': df})
        if isinstance(result, pd.Series):
            result = result.to_dict()
        elif isinstance(result, pd.DataFrame):
            result = result.to_dict(orient='records')
        return json.dumps({"results": result} if result else {"error": "No products found matching your criteria"})
    except Exception as e:
        return str(e)

# Query Generator Agent
query_generator_agent = Agent(
    name="query_generator_agent_v1",
    model="gemini-2.0-flash-exp",
    description="Handles data-related queries",
    instruction=(
        "You are a helpful assistant that can answer questions related to business data."
        f"Seeing the refined query, {df.columns} and {df.head()}, you generate a pandas expression to query the data."
    ),
    output_schema=QueryGeneratorOutput,
)

query_execution_agent = Agent(
    name="query_execution_agent_v1",
    model="gemini-2.0-flash-exp",
    description="Executes the query and returns the result",
    instruction=(
        "You are a helpful assistant that executes a pandas expression using the `execute_query` tool and return the results."
        "You should return the results in a human readable format. In a concise and convincing way."
    ),
    input_schema=QueryGeneratorOutput,
    tools=[execute_query]
)

data_query_agent = SequentialAgent(
    name="data_query_agent_v1",
    description="Orchestrates data query processing by sequentially invoking the query_refiner_agent_v1, query_generator_agent",
    sub_agents=[query_refiner_agent, query_generator_agent, query_execution_agent],
)

root_agent = Agent(
    name="general_agent_v1",
    model="gemini-2.0-flash-exp",
    description="Handles general conversation, promotes Muallim brand, and delegates data-related queries to `data_query_agent`",
    instruction=(
        "You are a friendly and talkative assistant representing Scentara, a premium perfume brand known for its exquisite fragrances. "
        "Introduce yourself as Scentara's brand representative and share our passion for creating unique, high-quality perfumes that captivate the senses. "
        "Engage users warmly, answer general questions, and encourage them to ask about our perfumes, collections, or anything related to the Scentara brand. "
        "If the user asks about perfumes and products of Scentara, delegate the query to `data_query_agent`. "
        "Always end your responses by asking an engaging question to keep the conversation going, such as 'What kind of fragrance are you looking for?' or 'Have you tried any of our signature scents yet?'"
    ),
    sub_agents=[data_query_agent]
)