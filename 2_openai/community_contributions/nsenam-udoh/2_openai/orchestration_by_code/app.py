import logging

import gradio as gr
from dotenv import load_dotenv

from research_manager import ResearchManager
from styles import CSS, EXAMPLES, HEADER_HTML, JS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
load_dotenv()


def _hidden_answers():
    return [gr.update(value="", visible=False) for _ in range(4)]

async def get_questions(query: str):
    try:
        result = await ResearchManager().clarify(query)
    except Exception as exc:
        return (f"Error while getting questions: {exc}", *_hidden_answers())

    updates = []
    for index in range(4):
        if index < len(result.questions):
            item = result.questions[index]
            updates.append(
                gr.update(label=item.question, placeholder=item.reason, value="", visible=True)
            )
        else:
            updates.append(gr.update(value="", visible=False))
    return (f"Answer any questions you choose, then run the research.", *updates)


async def run(query: str, *answers: str):
    status_lines = []
    pending = None
    async for update in ResearchManager().run(query, answers):
        if pending is not None:
            status_lines.append(pending)
            yield "\n".join(status_lines), ""
        pending = update

    if pending is not None:
        if pending.startswith("Error"):
            status_lines.append(pending)
            yield "\n".join(status_lines), ""
        else:
            yield "\n".join(status_lines), pending


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
        questions_button = gr.Button("Get questions", elem_id="dr-questions", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")
    clarification_status = gr.Markdown()
    answer_boxes = [
        gr.Textbox(label=f"Answer {index}", lines=2, visible=False)
        for index in range(1, 5)
    ]
    run_button = gr.Button("Run", variant="primary", elem_id="dr-run")
    status = gr.Markdown(label="Status")
    report = gr.Markdown(elem_id="dr-report", label="Report")

    questions_button.click(
        get_questions,
        inputs=query_textbox,
        outputs=[clarification_status, *answer_boxes],
    )
    run_button.click(
        run,
        inputs=[query_textbox, *answer_boxes],
        outputs=[status, report],
    )


if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
