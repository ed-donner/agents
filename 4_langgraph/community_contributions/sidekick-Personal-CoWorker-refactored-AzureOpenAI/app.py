import gradio as gr
from sidekick import Sidekick
import asyncio
from typing import Optional


async def setup_sidekick():
    """Initialize Sidekick on app load"""
    print("Setting up Sidekick...")
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(
    message: str,
    success_criteria: str,
    history: Optional[list],
    sidekick: Sidekick
) -> tuple:
    """
    Process user message and return updated chat history.
    Returns: (updated_history, cleared_message_box)
    """
    if not message or not success_criteria:
        return history or [], ""

    updated_history = await sidekick.run_superstep(
        message, success_criteria, history or []
    )
    return updated_history, ""  # Clear the message box after submission


async def reset_conversation(sidekick: Optional[Sidekick]):
    """Reset the conversation and create a new Sidekick instance"""
    if sidekick:
        await sidekick.cleanup()
    new_sidekick = await setup_sidekick()
    return [], "", "", new_sidekick  # chatbot, message, success_criteria, sidekick


async def free_resources(sidekick: Optional[Sidekick]) -> None:
    """Cleanup callback when app closes"""
    if sidekick:
        try:
            await sidekick.cleanup()
            print("Sidekick resources freed")
        except Exception as e:
            print(f"Error during cleanup: {e}")


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

with gr.Blocks(title="Sidekick - Personal Co-Worker") as ui:
    # State management
    sidekick = gr.State(value=None)

    # Header
    gr.Markdown("# 🤖 Sidekick Personal Co-Worker")
    gr.Markdown("Your AI assistant that completes tasks step-by-step with evaluation feedback.")

    # Chat interface
    with gr.Row():
        chatbot = gr.Chatbot(
            label="Conversation",
            height=400
        )

    # Input section
    with gr.Group():
        gr.Markdown("### Task Setup")
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Enter your request (e.g., 'Find the current Bitcoin price')",
                scale=4
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Define success (e.g., 'I need the price in USD and EUR')",
                scale=4
            )

    # Control buttons
    with gr.Row():
        reset_button = gr.Button("🔄 Reset", variant="stop", scale=1)
        submit_button = gr.Button("🚀 Submit", variant="primary", scale=1)

    # Info section
    gr.Markdown(
        """
        **How it works:**
        1. Enter your task in the request field
        2. Define what success looks like in the criteria field
        3. Click Submit or press Enter
        4. Sidekick will work through the task and provide feedback
        """
    )

    # Event handlers
    submit_button.click(
        fn=process_message,
        inputs=[message, success_criteria, chatbot, sidekick],
        outputs=[chatbot, message]
    )

    reset_button.click(
        fn=reset_conversation,
        inputs=[sidekick],
        outputs=[chatbot, message, success_criteria, sidekick]
    )

    # Initialize sidekick on load
    ui.load(fn=setup_sidekick, outputs=[sidekick])


if __name__ == "__main__":
    ui.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        css="""
        .header-text { text-align: center; margin-bottom: 20px; }
        .info-text { font-size: 14px; color: #666; }
        """
    )