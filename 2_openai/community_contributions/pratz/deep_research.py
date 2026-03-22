import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

async def start_clarification(query: str):
    manager = ResearchManager()
    questions = None

    async for chunk in manager.clarify(query):
        if chunk is None:
            return (
                manager,
                "Query is clear, ready to research.",
                gr.update(visible=False),
                gr.update(visible=True),   # show run button immediately
            )
        questions = chunk

    questions_md = "###Please answer these before we start:\n\n" + \
                   "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    return (
        manager,
        questions_md,
        gr.update(visible=True), 
        gr.update(visible=True),   
    )

async def submit_and_run(query: str, manager: ResearchManager, a1: str, a2: str, a3: str):
    answers = [a for a in [a1, a2, a3] if a.strip()]
    async for chunk in manager.run(query, answers):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("#  Deep Research")

    manager_state = gr.State(None)

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    start_button = gr.Button("Start", variant="primary")

    questions_display = gr.Markdown()

    with gr.Column(visible=False) as answers_col:
        answer1 = gr.Textbox(label="Answer 1")
        answer2 = gr.Textbox(label="Answer 2")
        answer3 = gr.Textbox(label="Answer 3")
        run_button = gr.Button("Run Research", variant="primary", visible=False)

    report = gr.Markdown(label="Report")

    start_button.click(
        fn=start_clarification,
        inputs=[query_textbox],
        outputs=[manager_state, questions_display, answers_col, run_button],
    )

    run_button.click(
        fn=submit_and_run,
        inputs=[query_textbox, manager_state, answer1, answer2, answer3],
        outputs=[report],
    )

ui.launch(inbrowser=True)
