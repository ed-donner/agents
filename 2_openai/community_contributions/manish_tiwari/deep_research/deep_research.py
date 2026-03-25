import os

import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str, clarification_answers: str = ""):
    """Two-step flow: leave answers empty to get 3 clarifying questions; then answer and run again."""
    ans = clarification_answers if clarification_answers is not None else ""
    async for chunk in ResearchManager().run(query, ans.strip() or None):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown(
        "# Deep Research\n\n"
        "1. Enter your topic and click **Run** to receive **three clarifying questions**.\n"
        "2. Answer them in the second box, then **Run** again to start the autonomous research loop "
        "(planner → parallel searches → writer → evaluator, up to 5 rounds), then email."
    )
    query_textbox = gr.Textbox(
        label="Research query",
        placeholder="e.g. Compare vector DBs for RAG in 2025",
    )
    answers_textbox = gr.Textbox(
        label="Clarification answers",
        lines=6,
        placeholder="After step 1, paste answers to each clarifying question here (numbered is fine).",
    )
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Output")

    run_button.click(fn=run, inputs=[query_textbox, answers_textbox], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, answers_textbox], outputs=report)

# Hugging Face Spaces sets PORT; bind 0.0.0.0 so the container accepts traffic.
_port = int(os.environ.get("PORT", "7860"))
ui.launch(server_name="0.0.0.0", server_port=_port, inbrowser=not os.environ.get("SPACE_ID"))
