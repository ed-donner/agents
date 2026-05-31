import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def get_clarification_questions(query):
    manager = ResearchManager()
    questions = await manager.get_clarifications(query)

    formatted = "\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(questions)]
    )

    return formatted


async def run(query: str, answers: str):
    async for chunk in ResearchManager().run(query, answers):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:

    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(
        label="What topic would you like to research?"
    )

    clarify_btn = gr.Button("Generate Clarifying Questions")
    clarify_output = gr.Markdown(label="Clarification Questions")

    clarify_btn.click(fn=get_clarification_questions, inputs=query_textbox, outputs=clarify_output)

    answers_box = gr.Textbox(label="Answer the clarifying questions", placeholder="1. ...\n2. ...\n3. ...")

    run_button = gr.Button("Run Research", variant="primary")

    report = gr.Markdown(label="Research Progress & Report")

    run_button.click(
        fn=run,
        inputs=[query_textbox, answers_box],
        outputs=report
    )

    query_textbox.submit(fn=run, inputs=[query_textbox, answers_box], outputs=report)


ui.launch(inbrowser=True)