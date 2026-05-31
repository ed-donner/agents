import asyncio
import argparse

from dotenv import load_dotenv

from agents import Runner, trace, gen_trace_id
from recipe_agents.search_agent import recipe_search_agent
from recipe_agents.writer_agent import recipe_writer_agent, RecipeData
from recipe_agents.email_agent import recipe_email_agent


class RecipeResearchManager:
    """
    Orchestrates:
    1. Web search for a recipe for a given cuisine.
    2. Synthesize a clean, cookable recipe.
    3. Email the recipe to the user.
    """

    async def run(self, cuisine: str, recipient_email: str) -> RecipeData:
        trace_id = gen_trace_id()
        with trace("Recipe deep research trace", trace_id=trace_id):
            print(f"Trace ID: {trace_id}")
            print(
                f"View trace at: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            )
            print(f"Starting recipe research for cuisine: {cuisine!r}")

            # 1) Build a single web search term
            search_term = f"best {cuisine} main dish recipe for home cooking"
            search_reason = (
                f"Find a popular, cookable main dish recipe in {cuisine} cuisine."
            )
            search_input = (
                f"Search term: {search_term}\nReason for searching: {search_reason}"
            )

            print(f"Running web search for: {search_term!r}")
            search_result = await Runner.run(
                recipe_search_agent,
                search_input,
            )
            summary_text = str(search_result.final_output)

            # 2) Ask writer agent to synthesize a single final recipe
            print("Synthesizing final recipe from web summary...")
            writer_input = (
                f"Cuisine: {cuisine}\n\n"
                "Here is a summary of one or more recipes from the web:\n\n"
                f"{summary_text}\n"
            )
            writer_result = await Runner.run(
                recipe_writer_agent,
                writer_input,
            )
            recipe: RecipeData = writer_result.final_output

            # 3) Convert recipe to markdown
            recipe_markdown = self._recipe_to_markdown(recipe)

            print("\n=== Final Recipe (Markdown) ===\n")
            print(recipe_markdown)

            # 4) Ask email agent to send the recipe
            print(f"\nSending recipe to {recipient_email}...")
            email_input = (
                f"Recipient email: {recipient_email}\n\n"
                f"Recipe in markdown:\n\n{recipe_markdown}"
            )
            email_result = await Runner.run(
                recipe_email_agent,
                email_input,
            )
            print("Email agent output:", email_result.final_output)

            print("\nDone.")
            return recipe

    def _recipe_to_markdown(self, recipe: RecipeData) -> str:
        """Render RecipeData into a markdown string."""
        lines: list[str] = []
        lines.append(f"# {recipe.title}")
        lines.append("")
        lines.append(f"_Cuisine_: {recipe.cuisine}")
        if recipe.servings:
            lines.append(f"_Servings_: {recipe.servings}")
        lines.append("")
        lines.append("## Ingredients")
        for ing in recipe.ingredients:
            if ing.notes:
                lines.append(f"- {ing.quantity} {ing.name} ({ing.notes})")
            else:
                lines.append(f"- {ing.quantity} {ing.name}")
        lines.append("")
        lines.append("## Steps")
        for i, step in enumerate(recipe.steps, start=1):
            lines.append(f"{i}. {step}")
        lines.append("")
        lines.append("## Shopping List")
        lines.append(recipe.shopping_list_markdown)
        return "\n".join(lines)


if __name__ == "__main__":
    # Load environment variables (OPENAI_API_KEY, SENDGRID_API_KEY, etc.)
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Deep research for recipes")
    parser.add_argument("--cuisine", required=True, help="Cuisine name, e.g. 'Italian'")
    parser.add_argument("--email", required=True, help="Destination email address")
    args = parser.parse_args()

    manager = RecipeResearchManager()
    asyncio.run(manager.run(args.cuisine, args.email))
