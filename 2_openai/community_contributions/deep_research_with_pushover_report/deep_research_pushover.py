#!/usr/bin/env python3
"""
Deep Research with Pushover Notifications

Web interface for the deep research system with Pushover notifications.
Launch this script to get a Gradio web interface where you can enter research queries
and receive the results both in the browser and as Pushover notifications.

Make sure you have PUSHOVER_TOKEN and PUSHOVER_USER in your .env file.
"""

import gradio as gr
import asyncio
from dotenv import load_dotenv
from pushover_research_manager import PushoverResearchManager

load_dotenv(override=True)


async def run_research(query: str):
    """Run the research process and yield status updates"""
    if not query.strip():
        yield "❌ Please enter a research query."
        return
        
    manager = PushoverResearchManager()
    async for chunk in manager.run(query):
        yield chunk


async def run_research_generator(query: str):
    """Generator version for Gradio streaming"""
    result = ""
    async for chunk in run_research(query):
        result = chunk
        yield result


def sync_research_wrapper(query: str):
    """Synchronous wrapper for Gradio compatibility"""
    async def _run():
        result = ""
        async for chunk in run_research(query):
            result = chunk
        return result
    
    return asyncio.run(_run())


# Create the Gradio interface
with gr.Blocks(
    title="Deep Research with Pushover",
    css="""
    .gradio-container {
        max-width: 900px !important;
    }
    """
) as ui:
    
    gr.Markdown(
        """
        # 🔍 Deep Research with Pushover Notifications
        
        Enter a research topic below and get:
        - **Live updates** in this interface
        - **Detailed report** displayed here  
        - **Pushover notification** sent to your device 📱
        
        Make sure you have `PUSHOVER_TOKEN` and `PUSHOVER_USER` configured in your `.env` file.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=4):
            query_textbox = gr.Textbox(
                label="🎯 What would you like to research?",
                placeholder="e.g., Latest AI Agent frameworks in 2025",
                lines=2
            )
        with gr.Column(scale=1):
            run_button = gr.Button("🚀 Start Research", variant="primary", size="lg")
    
    gr.Markdown("### 📊 Research Progress & Results")
    
    report_output = gr.Markdown(
        label="Report", 
        value="Enter a research query above and click 'Start Research' to begin...",
        container=True
    )
    
    # Set up the event handlers
    run_button.click(
        fn=sync_research_wrapper, 
        inputs=query_textbox, 
        outputs=report_output,
        show_progress="full"
    )
    
    query_textbox.submit(
        fn=sync_research_wrapper, 
        inputs=query_textbox, 
        outputs=report_output,
        show_progress="full"
    )
    
    gr.Markdown(
        """
        ---
        **💡 Pro Tips:**
        - Research typically takes 1-3 minutes
        - You'll get a Pushover notification when complete
        - Check the trace link for detailed execution logs
        - The full report is also displayed above
        """
    )


if __name__ == "__main__":
    print("🚀 Launching Deep Research with Pushover interface...")
    print("📱 Make sure your Pushover credentials are configured!")
    ui.launch(inbrowser=True, share=False)
