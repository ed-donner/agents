import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()

load_dotenv(override=True)

# Global variable to store the current query for the two-step process
current_query = None

async def run(query: str):
    """First step: Generate clarifying questions"""
    global current_query
    current_query = query
    
    async for chunk in ResearchManager().run(query):
        yield chunk

async def process_clarifications(clarifying_answers: str):
    """Second step: Process user clarifications and run research"""
    global current_query
    
    if current_query is None:
        yield "Error: No query found. Please start a new research query."
        return
    
    # Parse the clarifying answers (assuming they're provided as numbered responses)
    answers = []
    lines = clarifying_answers.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):  # Skip empty lines and comments
            # Remove numbering if present (e.g., "1. ", "1) ", etc.)
            import re
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            if line:
                answers.append(line)
    
    if len(answers) < 3:
        yield f"Please provide answers to all 3 clarifying questions. You provided {len(answers)} answers."
        return
    
    # Run the research with clarifications
    async for chunk in ResearchManager().run(current_query, answers):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research with Clarifying Questions")
    
    with gr.Tab("Step 1: Ask Questions"):
        gr.Markdown("### Enter your research topic")
        query_textbox = gr.Textbox(label="What topic would you like to research?", placeholder="e.g., AI trends in 2024")
        run_button = gr.Button("Generate Clarifying Questions", variant="primary")
        questions_output = gr.Markdown(label="Clarifying Questions")
        
        run_button.click(fn=run, inputs=query_textbox, outputs=questions_output)
        query_textbox.submit(fn=run, inputs=query_textbox, outputs=questions_output)
    
    with gr.Tab("Step 2: Provide Answers"):
        gr.Markdown("### Answer the clarifying questions")
        gr.Markdown("Please provide your answers to the clarifying questions from Step 1. You can format them as numbered responses or just separate lines.")
        clarifying_answers_textbox = gr.Textbox(
            label="Your Answers to Clarifying Questions", 
            placeholder="1. [Your answer to question 1]\n2. [Your answer to question 2]\n3. [Your answer to question 3]",
            lines=5
        )
        process_button = gr.Button("Process Answers & Run Research", variant="primary")
        research_output = gr.Markdown(label="Research Results")
        
        process_button.click(fn=process_clarifications, inputs=clarifying_answers_textbox, outputs=research_output)

ui.launch(inbrowser=True)

