from dotenv import load_dotenv
load_dotenv(override=True)  # load .env before anything else

import gradio as gr
from kids_manager import JoyfulKidsManager

manager = JoyfulKidsManager()

async def run_series(theme: str, ages: str, duration: int):
    async for chunk in manager.run_series(
        series_theme=theme,
        ages=ages,
        duration_minutes=int(duration),
    ):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("""
# 🌟 Joyful Kids Bible – Family Series Generator

Create a 5-day **family Bible playtime series** for your little ones.

1. Pick a theme (Christmas, Easter, Thankfulness, etc.).
2. Choose your kids' ages.
3. Choose how long you'd like each day to be.

You'll receive:
- 5 days of simple stories, games, activities, and verse memory ideas  
- A **suggested calendar reminder** (title + time + duration) you can add to your calendar
""")

    theme_dd = gr.Dropdown(
        label="Series theme or holiday",
        choices=[
            "Christmas",
            "Easter",
            "Thankfulness / Gratitude",
            "Kindness & Sharing",
            "Fruit of the Spirit",
            "Everyday Jesus' love",
            "Courage & Trusting God",
            "Joy & Praise",
        ],
        value="Christmas",
        info="Choose the general theme for this 5-day series.",
    )

    ages_dd = gr.Dropdown(
        label="Kids' ages",
        choices=[
            "2–3 years old",
            "3–4 years old",
            "4–5 years old",
            "5–6 years old",
            "6–7 years old",
        ],
        value="3–4 years old",
        info="Choose the age range that best matches your kids.",
    )


    duration_slider = gr.Slider(
        minimum=5,
        maximum=40,
        value=15,
        step=5,
        label="Approx. duration per day (minutes)",
    )

    run_btn = gr.Button("Generate 5-Day Family Bible Series 🎁", variant="primary")
    output_md = gr.Markdown(label="Preview")

    run_btn.click(
        fn=run_series,
        inputs=[theme_dd, ages_dd, duration_slider],
        outputs=output_md,
    )

ui.launch(inbrowser=True)
