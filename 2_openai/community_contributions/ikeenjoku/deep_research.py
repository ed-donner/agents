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


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    search_button = gr.Button("Search", variant="primary")

    gr.Markdown("# Clarifying Questions")
    clarifying_questions = gr.Markdown(label="Clarifying Questions")
    query_textbox.submit(fn=ask_clarifying_questions, inputs=query_textbox, outputs=clarifying_questions)
    search_button.click(fn=ask_clarifying_questions, inputs=query_textbox, outputs=clarifying_questions)

    clarifying_answers_textbox = gr.Textbox(label="Answer the following clarifying questions for an even better research result")
    start_research_button = gr.Button("Start research", variant="primary")

    gr.Markdown("# Research Report")
    report = gr.Markdown(label="Research Report")
    start_research_button.click(fn=start_research, inputs=[query_textbox, clarifying_questions, clarifying_answers_textbox], outputs=report)
    clarifying_answers_textbox.submit(fn=start_research, inputs=[query_textbox, clarifying_questions, clarifying_answers_textbox], outputs=report)

ui.launch(inbrowser=True)

