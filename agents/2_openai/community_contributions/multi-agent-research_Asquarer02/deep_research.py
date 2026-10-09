import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

async def get_clarifying_questions(query: str):
    """Get clarifying questions for the research query"""
    manager = ResearchManager()
    questions_text = ""
    async for chunk in manager.run(query):
        if "Please provide answers" in chunk:
            questions_text += "\nPlease provide your answers to these questions to continue with the research."
            yield questions_text
            return
        questions_text += chunk + "\n"
        yield questions_text

async def do_research(query: str, clarification_answers: str):
    """Run the research process with the given query and clarification answers"""
    manager = ResearchManager()
    async for chunk in manager.run(query, clarification_answers):
        yield chunk

# Custom CSS for better styling
custom_css = """
:root {
    --background-primary: #1a1a1a;
    --background-secondary: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #b3b3b3;
    --border-color: #404040;
    --accent-color: #3498db;
    --accent-hover: #2980b9;
}

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    background: var(--background-primary) !important;
    color: var(--text-primary) !important;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: var(--background-secondary);
    border-radius: 10px;
    border: 1px solid var(--border-color);
}

.header h1 {
    color: var(--text-primary);
    font-size: 2.5em;
    margin-bottom: 10px;
}

.header p {
    color: var(--text-secondary);
    font-size: 1.1em;
}

.section {
    background: var(--background-secondary);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid var(--border-color);
}

.section-title {
    color: var(--text-primary);
    font-size: 1.2em;
    margin-bottom: 15px;
    font-weight: 600;
}

.button-primary {
    background: var(--accent-color) !important;
    color: white !important;
    border: none !important;
    padding: 10px 20px !important;
    border-radius: 5px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.button-primary:hover {
    background: var(--accent-hover) !important;
    transform: translateY(-1px) !important;
}

.output-box {
    background: var(--background-primary) !important;
    border-radius: 8px !important;
    padding: 15px !important;
    margin-top: 10px !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* Input field styling */
input[type="text"], textarea {
    background: var(--background-primary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
}

input[type="text"]:focus, textarea:focus {
    border-color: var(--accent-color) !important;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2) !important;
}

/* Label styling */
label {
    color: var(--text-primary) !important;
}

/* Progress indicator */
.progress {
    color: var(--text-secondary) !important;
    font-style: italic;
}
"""

with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=custom_css) as ui:
    with gr.Column(elem_classes="container"):
        # Header
        with gr.Column(elem_classes="header"):
            gr.Markdown("# 🔍 Enhanced Deep Research")
            gr.Markdown("Enter your research query and get comprehensive results with AI-powered analysis")
        
        # Step 1: Query Input
        with gr.Column(elem_classes="section"):
            gr.Markdown("### Step 1: Enter Your Research Query", elem_classes="section-title")
            query_textbox = gr.Textbox(
                label="What topic would you like to research?",
                placeholder="Enter your research query here...",
                lines=3
            )
            get_questions_button = gr.Button(
                "Get Clarifying Questions",
                variant="primary",
                elem_classes="button-primary"
            )
        
        # Step 2: Clarifying Questions
        with gr.Column(elem_classes="section"):
            gr.Markdown("### Step 2: Review Clarifying Questions", elem_classes="section-title")
            questions_output = gr.Markdown(
                label="Clarifying Questions",
                elem_classes="output-box"
            )
        
        # Step 3: Provide Answers
        with gr.Column(elem_classes="section"):
            gr.Markdown("### Step 3: Provide Your Answers", elem_classes="section-title")
            clarification_answers = gr.Textbox(
                label="Answers to Clarifying Questions",
                placeholder="Enter your answers to the clarifying questions here...",
                lines=5
            )
            do_research_button = gr.Button(
                "Start Research",
                variant="primary",
                elem_classes="button-primary"
            )
        
        # Step 4: Research Results
        with gr.Column(elem_classes="section"):
            gr.Markdown("### Step 4: Research Results", elem_classes="section-title")
            report = gr.Markdown(
                label="Research Report",
                elem_classes="output-box"
            )
        
        # Progress indicator
        # with gr.Column(elem_classes="section"):
        #     gr.Markdown("### Progress", elem_classes="section-title")
        #     progress = gr.Markdown("Waiting to start...", elem_classes="progress")
    
    # Event handlers
    get_questions_button.click(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=questions_output
    )
    query_textbox.submit(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=questions_output
    )
    
    do_research_button.click(
        fn=do_research,
        inputs=[query_textbox, clarification_answers],
        outputs=report
    )

ui.launch(inbrowser=True, share=True)