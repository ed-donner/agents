import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager, ClarifyingQuestions
from styles import CSS, JS, EXAMPLES, HEADER_HTML

load_dotenv(override=True)

async def clarfying_questions(query: str):
     async for status_update in ClarifyingQuestions().run(query):
        yield status_update
         

async def run(query: str):
    async for status_update in ResearchManager().run(query):
        yield status_update

def show_question(name):
    return (
        gr.update(visible=True),
        gr.update(label=f"היי {name}, מה תרצה לחקור היום?")
    )

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

    # clarfyiers = gr.Markdown(elem_id="dr-clarfyiers")
    clarfyiers = gr.State([])

    run_button.click(clarfying_questions, inputs=query_textbox, outputs=clarfyiers)
    query_textbox.submit(clarfying_questions, inputs=query_textbox, outputs=clarfyiers)

    clarifiers_display = gr.Markdown(elem_id="dr-clarfyiers")  # מציג רק מחרוזת אחת בכל פעם
    user_box = gr.Textbox(label="Ans")
    submit_btn = gr.Button("Submit")

    # answers = gr.State({})
    # def next_step(text, ans):
    #     idx = len(ans)
    #     if idx < len(clarfyiers):
    #         ans[clarfyiers[idx]] = text

    #     next_idx = len(ans)
    #     if next_idx < len(clarfyiers):
    #         return clarfyiers[next_idx], "", ans
    #     return "Done!", "", ans

    # btn.click(next_step, inputs=[user_box, answers], outputs=[prompt_txt, user_box, answers])

    # report = gr.Markdown(elem_id="dr-report")

    # run_button.click(run, inputs=query_textbox, outputs=report)
    # query_textbox.submit(run, inputs=query_textbox, outputs=report)


if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
