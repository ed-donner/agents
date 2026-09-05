import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()


async def get_clarifications(query: str):
    """ Stage 1: ask the clarifier agent for questions and reveal the answer panel. """
    questions = await manager.clarify(query)
    questions = (questions + ["", "", ""])[:3]  # be defensive about the count
    return (
        questions,
        gr.update(visible=True),
        gr.update(label=questions[0], value=""),
        gr.update(label=questions[1], value=""),
        gr.update(label=questions[2], value=""),
    )


async def run_research(query: str, questions: list[str], a1: str, a2: str, a3: str):
    """ Stage 2: run the full pipeline with the query and the user's answers. """
    async for chunk in manager.run(query, questions, [a1, a2, a3]):
        yield chunk


with gr.Blocks() as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Get clarifying questions", variant="primary")

    questions_state = gr.State([])
    with gr.Column(visible=False) as clarify_panel:
        gr.Markdown("**Please answer these clarifying questions, then run the research:**")
        answer1 = gr.Textbox(label="Answer 1")
        answer2 = gr.Textbox(label="Answer 2")
        answer3 = gr.Textbox(label="Answer 3")
        research_button = gr.Button("Run research", variant="primary")
    report = gr.Markdown(label="Report")

    clarify_button.click(
        fn=get_clarifications,
        inputs=query_textbox,
        outputs=[questions_state, clarify_panel, answer1, answer2, answer3],
    )
    research_button.click(
        fn=run_research,
        inputs=[query_textbox, questions_state, answer1, answer2, answer3],
        outputs=report,
    )

ui.launch(theme=gr.themes.Default(primary_hue="sky"), inbrowser=True)
