import gradio as gr
from dotenv import load_dotenv
from Research_Manager import Research_manager
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

load_dotenv(override=True)

# Custom light-mode CSS optimized for high text-readability and crisp contrast
CUSTOM_CSS = """
body, .gradio-container {
    background-color: #FAFAFA !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}
.chat-container {
    max-width: 820px !important;
    margin: 0 auto !important;
    padding-top: 2.5rem !important;
}
.research-header {
    text-align: center;
    margin-bottom: 2.5rem;
}
.research-header h1 {
    font-weight: 700 !important;
    color: #111827 !important;
    letter-spacing: -0.03em !important;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
}
.research-header p {
    color: #4B5563 !important;
    font-size: 1.05rem !important;
}
.status-card {
    background-color: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
    border-radius: 0.75rem !important;
    padding: 0.75rem 1.2rem !important;
    margin-bottom: 2rem !important;
}
.status-text textarea {
    background-color: transparent !important;
    border: none !important;
    color: #1D4ED8 !important;
    font-family: "SF Mono", SFMono-Regular, Consolas, monospace !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    resize: none !important;
}
.report-output {
    color: #1F2937 !important;
    font-size: 1.1rem !important;
    line-height: 1.8 !important;
    padding: 1.5rem !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 0.75rem !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
}
.report-output h1, .report-output h2, .report-output h3 {
    color: #111827 !important;
    font-weight: 700 !important;
    margin-top: 1.75rem !important;
    margin-bottom: 0.75rem !important;
}
.report-output p {
    margin-bottom: 1.25rem !important;
}
.input-bar {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 1.25rem !important;
    box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.05) !important;
    padding: 0.4rem !important;
}
.input-bar textarea {
    background-color: transparent !important;
    border: none !important;
    color: #111827 !important;
    font-size: 1.05rem !important;
}
.input-bar textarea:focus {
    box-shadow: none !important;
}
"""

async def run(query: str):
    """ Streams agent state transitions and wraps safety loop violations gracefully """
    manager = Research_manager()
    full_report = ""
    
    try:
        async for chunk in manager.run(query):
            if chunk.startswith("#") or len(chunk) > 300:
                full_report += chunk + "\n\n"
                yield full_report, "✨ Analysis complete."
            else:
                yield full_report, f"📡 {chunk}"
                
    except InputGuardrailTripwireTriggered:
        yield "", "🛑 [Input Guardrail Blocked] This sensitive query cannot be processed."
        
    except OutputGuardrailTripwireTriggered:
        yield (
            "⚠️ **Guardrail Exception**: The final report was blocked because it violated formatting "
            "rules (e.g., contained emojis). Please try modifying your query.",
            "🛑 [Output Guardrail Blocked] Formatting restrictions triggered."
        )

# Crisp clean native light theme configuration
light_theme = gr.themes.Default(primary_hue="blue", neutral_hue="slate").set(
    body_background_fill="#FAFAFA",
    block_background_fill="#FFFFFF",
    block_border_color="#E5E7EB",
    input_background_fill="#FFFFFF",
    button_primary_background_fill="#1D4ED8",
    button_primary_background_fill_hover="#1E40AF",
    button_primary_text_color="#FFFFFF"
)

with gr.Blocks(theme=light_theme, css=CUSTOM_CSS) as ui:
    with gr.Column(elem_classes="chat-container"):
        
        gr.HTML(
            """
            <div class="research-header">
                <h1>Deep Research</h1>
                <p>Thinking engine for deep synthesis and automated intelligence gathering</p>
            </div>
            """
        )
            
        with gr.Row(elem_classes="input-bar"):
            query_textbox = gr.Textbox(
                show_label=False,
                placeholder="What would you like to research deeply? Press Enter to run...",
                lines=2,
                max_lines=6,
                scale=8
            )
            run_button = gr.Button("↑", variant="primary", scale=1)
            
        gr.Markdown("<br>")
        
        with gr.Row(elem_classes="status-card"):
            with gr.Column():
                status_logs = gr.Textbox(
                    show_label=False,
                    placeholder="System standing by...",
                    interactive=False,
                    lines=1,
                    elem_classes="status-text"
                )
                
        with gr.Column():
            report_display = gr.Markdown(value="", elem_classes="report-output")

    execution_args = {
        "fn": run,
        "inputs": query_textbox,
        "outputs": [report_display, status_logs],
        "show_progress": "minimal"
    }
    
    run_button.click(**execution_args)
    query_textbox.submit(**execution_args)

if __name__ == "__main__":
    ui.queue().launch(inbrowser=True)
