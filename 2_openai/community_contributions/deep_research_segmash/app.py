import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from clarification_agent import ClarificationData
from styles import CSS, JS, EXAMPLES, HEADER_HTML

load_dotenv(override=True)

# Filled in by start(); reused by answer() for the same research session.
manager = None

# Output slots shared by both handlers: [clarify_box, question_radio, status, answer_button, report]
OUTPUTS = ["dr-clarify", "dr-question", "dr-status", "dr-answer", "dr-report"]


def render_question(data) -> tuple:
    """Turn a ClarificationData into (clarify_visible, radio_update, status_text, controls_update)."""
    if data.question and data.options:
        status = f"**Clarification needed:** {data.question}"
        radio = gr.update(choices=data.options, value=None, visible=True)
        return gr.update(visible=True), radio, status, gr.update(visible=True)
    # No more questions -> hide the answer controls.
    status = f"**Query clarified:** {data.query}\n\nStarting research..."
    radio = gr.update(choices=[], value=None, visible=False)
    return gr.update(visible=False), radio, status, gr.update(visible=False)


async def emit(data):
    """Yield the Gradio outputs for a result: a final report string, or a clarification question."""
    if type(data) is not ClarificationData:
        # Report case -> hide the question and the answer button, show the report.
        yield gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), data
    else:
        clarify, radio, status, controls = render_question(data)
        yield clarify, radio, status, controls, gr.update()


async def start(query: str):
    """Start clarification with a FRESH manager and show the first question (if any)."""
    if not query or not query.strip():
        yield gr.update(visible=False), gr.update(visible=False), "Please enter a research topic.", gr.update(visible=False), gr.update()
        return

    global manager
    manager = ResearchManager()

    data = None
    async for update in manager.run(query):
        data = update
    async for outputs in emit(data):
        yield outputs


async def answer(choice: str):
    """Feed the chosen option back. Show the next question, or run the research stage."""
    if not choice:
        raise gr.Error("Please choose an option first.")
    async for update in manager.answer(choice):
        data = update
    async for outputs in emit(data):
        yield outputs


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

    gr.HTML('<div class="dr-examples-label">Try one</div>')
    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

    # Status line for stage updates.
    status = gr.Markdown(elem_id="dr-status")

    # Clarification card: question + options + submit (hidden until the agent asks).
    with gr.Column(elem_id="dr-clarify", visible=False) as clarify_box:
        question_radio = gr.Radio(
            label="Choose an answer",
            choices=[],
            show_label=True,
            elem_id="dr-question",
            visible=False,
        )
        answer_button = gr.Button("Submit answer", elem_id="dr-answer", visible=False)

    report = gr.Markdown(elem_id="dr-report")

    # Submit (Enter) starts clarification -- no separate "Run" button.
    query_textbox.submit(
        start,
        inputs=query_textbox,
        outputs=[clarify_box, question_radio, status, answer_button, report],
    )
    answer_button.click(
        answer,
        inputs=question_radio,
        outputs=[clarify_box, question_radio, status, answer_button, report],
    )


if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
