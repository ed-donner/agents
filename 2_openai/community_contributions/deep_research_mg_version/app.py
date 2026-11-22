import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager, ClarifyingQuestions
from styles import CSS, JS, EXAMPLES, HEADER_HTML

load_dotenv(override=True)

async def clarfying_questions(query: str):
    if not query or not query.strip():
        yield (
            gr.update(value="", visible=False),
            gr.update(value="", visible=False),
            gr.update(visible=False),
        )
        return

    async for status_update in ClarifyingQuestions().run(query):
        yield (
            gr.update(value=status_update, visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )
         

async def run(query: str, clarify_q: str, clarify_a: str):
    async for status_update in ResearchManager().run(query, clarify_q, clarify_a):
        yield status_update

with gr.Blocks(title="Deep Research") as ui:
    gr.HTML(HEADER_HTML)

    with gr.Row(elem_classes="dr-query-row"):
        query_textbox = gr.Textbox(
            placeholder="Type a research question...",
            show_label=False,
            container=False,
            autofocus=True,
            elem_id="dr-query",
            scale=5,
        )
        run_button = gr.Button("Investigate", variant="primary", elem_id="dr-run", scale=1)

    gr.HTML('<div class="dr-examples-label">Try one</div>')
    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

    clarifiers_display = gr.Markdown(elem_id="dr-clarfyiers", visible=False)
    user_box = gr.Textbox(label="Your Answer Here", visible=False)
    submit_btn = gr.Button("Submit", visible=False)

    clarfyiers_ans = gr.State([])
    report = gr.Markdown(elem_id="dr-report")
    run_button.click(
        clarfying_questions,
        inputs=query_textbox,
        outputs=[clarifiers_display, user_box, submit_btn],
    )
    query_textbox.submit(
        clarfying_questions,
        inputs=query_textbox,
        outputs=[clarifiers_display, user_box, submit_btn],
    )
    submit_btn.click(
        run,
        inputs=[query_textbox, clarifiers_display, user_box],
        outputs=report,
    )
    user_box.submit(
        run,
        inputs=[query_textbox, clarifiers_display, user_box],
        outputs=report,
    )

if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
