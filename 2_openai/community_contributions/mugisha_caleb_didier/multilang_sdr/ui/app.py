import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv(override=True)

import gradio as gr
from core.pipeline import run_pipeline


async def run(prospect_info: str):
    async for chunk in run_pipeline(prospect_info):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown(
        "# Multi-Language Cold Email Generator\n\n"
        "Generate cold sales emails in 3 languages using different models. "
        "All drafts are translated to English for fair judging, then the "
        "winner is delivered in your input language.\n\n"
        "| Language | Model | Provider |\n"
        "|----------|-------|----------|\n"
        "| English | gpt-4o-mini | OpenAI |\n"
        "| French | gemini-2.0-flash | Google (via OpenRouter) |\n"
        "| Kinyarwanda | claude-sonnet-4 | Anthropic (via OpenRouter) |"
    )

    prospect_input = gr.Textbox(
        label="Prospect Info",
        placeholder="Describe the prospect: company, role, industry, pain points...",
        lines=4,
    )

    with gr.Row():
        run_button = gr.Button("Generate & Send Best Email", variant="primary")
        clear_button = gr.ClearButton(value="Clear")

    gr.Examples(
        examples=[
            [
                "Sarah Chen, VP of Engineering at DataFlow Inc, a mid-size data analytics "
                "startup in San Francisco. They recently raised Series B and are scaling "
                "their engineering team from 20 to 50. Pain points: slow hiring pipeline, "
                "no structured onboarding, engineers spending too much time on repetitive tasks."
            ],
            [
                "Jean-Pierre Moreau, Directeur Commercial chez TechVision SA, une entreprise "
                "de logiciels B2B basee a Paris avec 200 employes. Ils cherchent a automatiser "
                "leur processus de prospection et reduire le cycle de vente."
            ],
            [
                "James Kamanzi, Umuyobozi Mukuru (CEO) wa KigaliTech Solutions"
                "ikigo cy'inama n'ubuhanga mu ikoranabuhanga gikura i Kigali, Rwanda, gifite abakozi 30."
                "Bakorera banki zo mu Afurika y'Uburasirazuba kandi bakeneye ibikoresho byiza byo gucunga imishinga no gutumanahana n'abakiriya."
            ],
        ],
        inputs=prospect_input,
    )

    output = gr.Markdown(label="Results")
    clear_button.add(components=[prospect_input, output])

    run_button.click(fn=run, inputs=prospect_input, outputs=output)
    prospect_input.submit(fn=run, inputs=prospect_input, outputs=output)

ui.launch(inbrowser=True)
