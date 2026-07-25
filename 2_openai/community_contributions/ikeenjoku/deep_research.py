import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def start_research(query: str, clarifying_questions: str, clarifying_answers: str):
    research_params = f"Initial query: {query}\n\nClarifying questions: {clarifying_questions}\n\nClarifying answers: {clarifying_answers}"
    try:
        async for chunk in ResearchManager().start_research(research_params):
            yield chunk
    except Exception as e:
        print("Error with start_research", e)


async def ask_clarifying_questions(query: str):
    return await ResearchManager().generate_clarifying_questions(query)


async def show_clarifying_questions(query: str):
    """Generate clarifying questions and show the section"""
    questions = await ResearchManager().generate_clarifying_questions(query)
    return {
        clarifying_section: gr.update(visible=True),
        clarifying_questions: questions
    }


async def run_research(query: str, clarifying_questions: str, clarifying_answers: str):
    """Run research and show the report section"""
    # Show the report section immediately
    yield {
        report_section: gr.update(visible=True),
        report: "Starting research..."
    }

    # Stream research updates
    async for chunk in start_research(query, clarifying_questions, clarifying_answers):
        yield {
            report_section: gr.update(visible=True),
            report: chunk
        }


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    search_button = gr.Button("Search", variant="primary")

    # Clarifying Questions Section (initially hidden)
    with gr.Group(visible=False) as clarifying_section:
        gr.Markdown("# Clarifying Questions")
        clarifying_questions = gr.Markdown(label="Clarifying Questions")
        clarifying_answers_textbox = gr.Textbox(label="Answer the following clarifying questions for an even better research result")
        start_research_button = gr.Button("Start research", variant="primary")

    # Research Report Section (initially hidden)
    with gr.Group(visible=False) as report_section:
        gr.Markdown("# Research Report")
        report = gr.Markdown(label="Research Report")

    # Event handlers
    query_textbox.submit(
        fn=show_clarifying_questions,
        inputs=query_textbox,
        outputs=[clarifying_section, clarifying_questions]
    )
    search_button.click(
        fn=show_clarifying_questions,
        inputs=query_textbox,
        outputs=[clarifying_section, clarifying_questions]
    )
    start_research_button.click(
        fn=run_research,
        inputs=[query_textbox, clarifying_questions, clarifying_answers_textbox],
        outputs=[report_section, report]
    )
    clarifying_answers_textbox.submit(
        fn=run_research,
        inputs=[query_textbox, clarifying_questions, clarifying_answers_textbox],
        outputs=[report_section, report]
    )

ui.launch(inbrowser=True)

