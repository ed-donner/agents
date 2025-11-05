import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):

    async for chunk in ResearchManager().run(query):
        yield chunk


# Example queries for users
example_queries = [
    "Patient has non-small cell lung cancer (NSCLC) with an EGFR T790M mutation. What are the indicated therapies and resistance mechanisms?",
    "What are the treatment options for metastatic melanoma with BRAF V600E mutation?",
    "Breast cancer patient with HER2 amplification - what targeted therapies are available and what are the latest clinical trials?",
    "Colorectal cancer with KRAS G12C mutation - what are the emerging treatment options?",
    "Patient with chronic myeloid leukemia (CML) has developed BCR-ABL T315I mutation. What are the resistance mechanisms and treatment alternatives?",
]

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("""
    <div class="medical-header">
        <h1>🧬 Pharmacogenomic Clinical Report Generator</h1>
        <p>AI-powered research system for oncology and precision medicine</p>
        <p style="font-size: 14px; opacity: 0.9;">
            Integrated searches across PubMed, ClinicalTrials.gov, and PharmGKB
        </p>
    </div>
    """)
    
    gr.Markdown("""
    ### What is this?
    This system generates comprehensive clinical pharmacogenomic reports by analyzing:
    - **PubMed**: Latest biomedical research and evidence
    - **ClinicalTrials.gov**: Active and completed clinical trials
    - **PharmGKB**: Pharmacogenomic drug-gene interactions
    
    ### How to use:
    Enter a clinical query about a cancer type, gene mutation, and desired research focus.
    The system will automatically parse your query, search relevant databases, and generate a detailed report.
    """)
    
    query_textbox = gr.Textbox(
        label="Clinical Query",
        placeholder="e.g., Patient has NSCLC with EGFR T790M mutation. What therapies are indicated?",
        lines=3
    )
    
    gr.Markdown('<div class="example-section"><strong>💡 Example Queries:</strong></div>')
    gr.Examples(
        examples=example_queries,
        inputs=query_textbox,
        label=None
    )
    
    run_button = gr.Button("🔬 Generate Clinical Report", variant="primary", size="lg")
    
    report = gr.Markdown(label="Clinical Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)
    
    gr.Markdown("""
    ---
    **Email**: Reports are automatically emailed upon completion (configure Mailgun settings in .env)
    
    **Saved Reports**: HTML reports are saved in the `reports/` directory
    """)

if __name__ == "__main__":
    ui.launch(inbrowser=True, share=False)
