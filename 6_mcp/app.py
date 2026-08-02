import warnings
import gradio as gr
from demo.ui import create_ui
from demo.util import css, js

# Gradio 6.14 reads a Starlette status constant that newer Starlette has renamed, so it warns on
# every request. Silence that upstream deprecation so the dashboard console stays clean.
warnings.filterwarnings("ignore", message=".*HTTP_422_UNPROCESSABLE_ENTITY.*")

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(
        theme=gr.themes.Default(primary_hue="sky"),
        css=css,
        js=js,
        inbrowser=True,
    )
