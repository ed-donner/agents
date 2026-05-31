import gradio as gr
from dotenv import load_dotenv
from medical_research_manager import MedicalResearchManager

load_dotenv(override=True)

async def run(query: str, email: str):
    """Run medical deep research and yield progress updates"""
    manager = MedicalResearchManager()
    async for chunk in manager.run(query, email):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as ui:
    gr.Markdown("# 🔬 Medical Deep Research - Academic Literature Review")
    gr.Markdown(
        "This tool conducts comprehensive research on medical topics by searching academic databases "
        "and peer-reviewed journals. Enter your medical query below to receive a detailed literature review report."
    )
    
    with gr.Row(scale=5):
        with gr.Column(scale=3):
            query_textbox = gr.Textbox(
                label="Medical Research Query",
                placeholder="e.g., 'Efficacy of mRNA vaccines in preventing severe COVID-19 outcomes' or 'Latest treatment protocols for type 2 diabetes'",
                lines=3
            )
        with gr.Column(scale=2):
            email_txt = gr.Textbox(
                label="Want a copy of this report? Just drop your email.",
                placeholder="you@example.com",
                scale=4
            )
    
    run_button = gr.Button("🔬 Start Medical Research", variant="primary", size="lg")
    report = gr.Markdown(label="Medical Literature Review Report")
    
    run_button.click(fn=run, inputs=[query_textbox, email_txt], outputs=report)
    query_textbox.submit(fn=run, inputs=[query_textbox, email_txt], outputs=report)
    email_txt.submit(fn=run, inputs=[query_textbox, email_txt], outputs=report)

ui.launch()

