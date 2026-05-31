import gradio as gr
from dotenv import load_dotenv

from recipe_manager import RecipeResearchManager

# Load environment variables (OPENAI_API_KEY, SENDGRID_API_KEY, etc.)
load_dotenv(override=True)

# Create a single manager instance to reuse between calls
manager = RecipeResearchManager()


async def generate_recipe(cuisine: str, email: str) -> str:
    """
    Gradio callback:
    - Takes cuisine + email from UI
    - Runs the async RecipeResearchManager
    - Returns the final recipe as markdown (plus a small status note)
    """
    cuisine = cuisine.strip()
    email = email.strip()

    if not cuisine:
        return "❌ Please enter a cuisine name (e.g. 'Italian', 'Idli Sambar')."
    if not email:
        return "❌ Please enter an email address."

    # Run the full pipeline (search -> synthesize -> email)
    recipe = await manager.run(cuisine, email)

    # Render markdown from the structured RecipeData
    recipe_markdown = manager._recipe_to_markdown(recipe)

    # Add a little note at the bottom
    recipe_markdown += (
        f"\n\n---\n\n✅ The recipe has been emailed to **{email}**.\n"
        "If you don't see it, please check your spam folder."
    )

    return recipe_markdown


# Define Gradio UI
demo = gr.Interface(
    fn=generate_recipe,
    inputs=[
        gr.Textbox(
            label="Cuisine",
            placeholder="e.g. Italian, Idli Sambar, Mexican",
        ),
        gr.Textbox(
            label="Email address",
            placeholder="you@example.com",
        ),
    ],
    outputs=gr.Markdown(label="Generated Recipe"),
    title="Deep Research for Recipes",
    description=(
        "Enter a cuisine and your email. The app will:\n"
        "1) Search the web for a suitable recipe\n"
        "2) Synthesize a clean, cookable recipe\n"
        "3) Email it to you as a nicely formatted HTML email."
    ),
)


if __name__ == "__main__":
    # Launch Gradio app
    demo.launch()
