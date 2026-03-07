"""Entry point for Hugging Face Spaces (and 'gradio run app.py')."""
from deep_research import ui

# On Spaces, the app is public by default; no need for share=True
ui.launch()
