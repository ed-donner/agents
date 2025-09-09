import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

async def do_research(query: str, refinement_questions: str, refinement_answers: str):
    research_input = f"Original Query: {query}\n\nRefinement Questions: {refinement_questions}\n\nRefinement Answers: {refinement_answers}"
    try:
        async for chunk in ResearchManager().do_research(research_input):
            yield chunk
    except Exception as e:
        print("Exception do_research:", e)

async def ask_refinement_questions(query: str):
    return await ResearchManager().generate_refinement_questions(query)

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research? ...(reports longer than 1000 words may be aborted.)")
    
    refinement_button = gr.Button("Refinement questions", variant="primary")
    gr.Markdown("# Refinement Questions")
    refinement_questions = gr.Markdown(label="Refinement Questions")
    query_textbox.submit(fn=ask_refinement_questions, inputs=query_textbox, outputs=refinement_questions)
    refinement_button.click(fn=ask_refinement_questions, inputs=query_textbox, outputs=refinement_questions)
    
    refinement_answers_textbox = gr.Textbox(label="Answer the refinement questions...")

    do_research_button = gr.Button("Do Research", variant="primary")
    gr.Markdown("# Report")
    report = gr.Markdown(label="Report")
    do_research_button.click(fn=do_research, inputs=[query_textbox, refinement_questions, refinement_answers_textbox], outputs=report)
    refinement_answers_textbox.submit(fn=do_research, inputs=[query_textbox, refinement_questions, refinement_answers_textbox], outputs=report)

ui.launch(inbrowser=True)

