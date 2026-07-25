"""Main entry point for the News Summarizer application."""

import gradio as gr
from dotenv import load_dotenv
from orchestrator import NewsSummaryOrchestrator

# Load environment variables
load_dotenv(override=True)


async def create_news_summary(topic: str) -> tuple[str, str | None]:
    """Gradio interface function for creating news summaries.
    
    Args:
        topic: News topic to summarize
        
    Returns:
        Tuple of (summary_text, audio_file_path) or (error_message, None)
    """
    try:
        orchestrator = NewsSummaryOrchestrator()
        summary, audio_path = await orchestrator.orchestrate(topic)
        return summary, audio_path
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)  # Log error for debugging
        return error_msg, None


# Custom theme with blue buttons
custom_theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="blue",
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
    button_primary_text_color="white",
)

# Gradio UI
demo = gr.Interface(
    fn=create_news_summary,
    inputs=gr.Dropdown(
        choices=["tech", "world", "business", "politics", "sports"],
        label="Select News Topic"
    ),
    outputs=[
        gr.Textbox(label="Summary (300 words)", lines=10),
        gr.Audio(label="2-Minute Audio Briefing", type="filepath")
    ],
    title="Multimodal Agent News Summarizer",
    description="Get a deep search of the latest news in your chosen topic and a 2-minute audio briefing",
    examples=[["tech"], ["world"], ["business"]],
    theme=custom_theme
)

if __name__ == "__main__":
    demo.launch()
