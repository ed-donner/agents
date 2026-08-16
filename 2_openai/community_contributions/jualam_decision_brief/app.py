from pathlib import Path

import gradio as gr
from dotenv import load_dotenv


ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV, override=True)

from brief_manager import BriefManager  # noqa: E402


async def create_brief(question: str, context: str):
    if not question or len(question.strip()) < 15:
        yield "Please enter a clear decision question (at least 15 characters)."
        return

    async for update in BriefManager().run(question, context):
        yield update


EXAMPLE_QUESTION = "Should a small software team prioritize a new AI feature or product reliability in 2026?"
EXAMPLE_CONTEXT = """We have six weeks before a customer demo, two backend developers, and
one frontend developer. Pilot customers requested the AI feature, but our background jobs
still fail occasionally. We want a credible demo without creating support problems."""


with gr.Blocks(title="Decision Brief Team") as ui:
    gr.Markdown(
        """# Decision Brief Team

Ask a decision question and optionally add your own context. The app performs five current
web searches, then strategy, risk, and execution agents produce one sourced decision brief.
Only the OpenAI API is used.
"""
    )

    question = gr.Textbox(
        label="Decision question",
        placeholder="What decision do you need to make?",
        lines=2,
    )
    context = gr.Textbox(
        label="Your context (optional)",
        placeholder="Add constraints, goals, facts, or background specific to your situation...",
        lines=8,
    )
    run_button = gr.Button("Create decision brief", variant="primary")
    output = gr.Markdown()

    gr.Examples(
        examples=[[EXAMPLE_QUESTION, EXAMPLE_CONTEXT]],
        inputs=[question, context],
    )

    run_button.click(create_brief, inputs=[question, context], outputs=output)


if __name__ == "__main__":
    ui.launch()
