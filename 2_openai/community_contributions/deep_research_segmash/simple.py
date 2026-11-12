import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from clarification_agent import ClarificationData


load_dotenv(override=True)
manager = None

def render_question(data) -> tuple:
    """Turn a ClarificationData into (radio_update, status_text, show_controls)."""
    if data.question and data.options:
        status = f"**Clarification needed:** {data.question}"
        radio = gr.update(choices=data.options, value=None, visible=True)
        return radio, status, gr.update(visible=True)
    # No more questions -> hide the answer controls.
    status = f"**Query clarified:** {data.query}\n\nStarting research..."
    radio = gr.update(choices=[], value=None, visible=False)
    return radio, status, gr.update(visible=False)


async def emit(data):
    print(f"emit: data:{data} type:{type(data)}")
    """Yield the Gradio outputs for a result: a final report string, or a clarification question."""
    if type(data) is not ClarificationData:
        # Report case -> hide the question and the answer button.
        yield gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), data
    else:
        radio, status, controls = render_question(data)
        yield radio, status, controls, gr.update()


async def start(query: str):
    """Start clarification and show the first question (if any)."""
    if not query or not query.strip():
        yield gr.update(visible=False), "Please enter a research topic.", gr.update(visible=False), gr.update()
        return
    
    data = None
    global manager
    manager = ResearchManager()
    async for update in manager.run(query):
        data = update
    async for outputs in emit(data):
        yield outputs
    print(f"data:{data} type:{type(data)}")



async def answer(choice: str):
    """Feed the chosen option back. Show the next question, or run the research stage."""
    if not choice:
        raise gr.Error("Please choose an option first.")
    async for update in manager.answer(choice):
        data = update
    async for outputs in emit(data):
        yield outputs
with gr.Blocks() as ui:
    gr.Markdown("## Deep Research")

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    status = gr.Markdown()

    # Dynamically populated question + options (hidden until the agent asks something).
    question_radio = gr.Radio(label="Choose an answer", choices=[], visible=False)
    answer_button = gr.Button("Submit answer", variant="secondary", visible=False)

    report = gr.Markdown(label="Report")

    # Submit (Enter) starts clarification -- no separate "Run" button.
    query_textbox.submit(
        start,
        inputs=query_textbox,
        outputs=[question_radio, status, answer_button, report],
    )
    answer_button.click(
        answer,
        inputs=question_radio,
        outputs=[question_radio, status, answer_button, report],
    )

ui.launch(theme=gr.themes.Default(primary_hue="sky"))

