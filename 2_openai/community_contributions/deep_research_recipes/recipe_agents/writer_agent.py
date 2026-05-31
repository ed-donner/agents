from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """
You are a chef who can synthesize a clear home-cooking recipe from web search summaries.

You will be given:
- The cuisine name.
- A short summary of one or more recipes from the web.

Your job:
1. Infer ONE good, representative main recipe for that cuisine.
2. Produce:
   - A descriptive title.
   - The approximate number of servings (if not obvious, assume 2–4).
   - A clear ingredient list with human-readable quantities.
   - A step-by-step set of instructions.
   - A simple shopping list (grouped logically, in markdown bullet list).

Guidelines:
- Use metric units where possible (g, ml, tbsp, tsp), but you can keep quantities
  a bit fuzzy (e.g. "1 small onion", "2 tbsp olive oil").
- Make instructions friendly and clear for a beginner home cook.
- Keep it roughly in the style of the given cuisine.
"""


class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient, e.g. 'olive oil'")
    quantity: str = Field(description="Human-readable amount, e.g. '2 tbsp', '500 g'")
    notes: str | None = Field(default=None, description="Optional notes, e.g. 'extra-virgin'")


class RecipeData(BaseModel):
    cuisine: str = Field(description="Cuisine name, e.g. 'Italian'")
    title: str = Field(description="Recipe title")
    servings: int | None = Field(default=None, description="Approximate number of servings")
    ingredients: list[Ingredient] = Field(description="List of ingredients with quantities")
    steps: list[str] = Field(description="Ordered cooking steps")
    shopping_list_markdown: str = Field(
        description="Shopping list as markdown bullet points (e.g. '- 500 g pasta')."
    )


recipe_writer_agent = Agent(
    name="RecipeWriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RecipeData,
)
