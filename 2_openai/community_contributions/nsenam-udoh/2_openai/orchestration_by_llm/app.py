import logging

import gradio as gr
from dotenv import load_dotenv

from manager_agent import ManagerTurn
from session import ManagerSession
from styles import CSS, EXAMPLES, HEADER_HTML, JS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
load_dotenv()


def _question_updates(turn: ManagerTurn):
    updates = []
    for index in range(4):
        if index < len(turn.questions):
            item = turn.questions[index]
            updates.append(
                gr.update(label=item.question, placeholder=item.reason, value="", visible=True)
            )
        else:
            updates.append(gr.update(value="", visible=False))
    return updates


async def run(query: str, session: ManagerSession | None, *answers: str):
    if session is None or session.status in {"final", "exhausted"}:
        session = ManagerSession()

    try:
        if session.status is None:
            turn = await session.start(query)
        else:
            turn = await session.answer(answers)
    except Exception as exc:
        turn = ManagerTurn(status="exhausted", report=f"Error: {exc}")

    report = turn.report or ""
    return (f"Status: {turn.status}", report, session, *_question_updates(turn))


with gr.Blocks(title="Deep Research") as ui:
    gr.HTML(HEADER_HTML)
    session_state = gr.State()

    with gr.Row(elem_classes="dr-query-row"):
        query_textbox = gr.Textbox(
            placeholder="Type a research question...",
            show_label=False,
            container=False,
            autofocus=True,
            elem_id="dr-query",
            scale=5,
        )
        run_button = gr.Button("Run", elem_id="dr-run", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")
    answer_boxes = [
        gr.Textbox(label=f"Answer {index}", lines=2, visible=False)
        for index in range(1, 5)
    ]
    status = gr.Markdown(label="Status")
    report = gr.Markdown(elem_id="dr-report", label="Report")

    run_button.click(
        run,
        inputs=[query_textbox, session_state, *answer_boxes],
        outputs=[status, report, session_state, *answer_boxes],
    )


if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
