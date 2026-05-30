"""
Gradio UI for the Intelligent Data Analysis Agent.
Supports clarifying questions, analysis plan display, and SQL preview.
"""
import gradio as gr
from sidekick import Sidekick
import asyncio


async def setup():
    """Initialize the Sidekick agent."""
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, history):
    """
    Process a message through the agent.
    Returns updated history and sidekick instance.
    """
    if not sidekick:
        sidekick = Sidekick()
        await sidekick.setup()

    # Run the analysis
    new_history, result = await sidekick.run_superstep(
        message=message,
        success_criteria=None,  # Success criteria embedded in agent logic now
        history=history
    )

    return new_history, sidekick


async def process_with_clarification(sidekick, message, clarifications, history):
    """
    Process a message with user-provided clarifications.
    Used when the user responds to clarifying questions.
    """
    if not sidekick:
        sidekick = Sidekick()
        await sidekick.setup()

    # Run the analysis with clarifications
    new_history, result = await sidekick.run_superstep(
        message=message,
        success_criteria=None,
        history=history,
        user_clarifications=clarifications
    )

    return new_history, sidekick


async def reset():
    """Reset the conversation."""
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", None, new_sidekick


def free_resources(sidekick):
    """Clean up resources when session ends."""
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


# Custom CSS for better styling
custom_css = """
.chatbot {
    height: 400px;
    overflow: auto;
}
.analysis-plan {
    font-family: monospace;
    background: #f5f5f5;
    padding: 10px;
    border-radius: 5px;
}
.sql-preview {
    font-family: monospace;
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 10px;
    border-radius: 5px;
}
"""


with gr.Blocks(
    title="Intelligent Data Analysis Agent",
    theme=gr.themes.Default(primary_hue="emerald"),
    css=custom_css
) as ui:
    gr.Markdown("# Intelligent Data Analysis Agent")
    gr.Markdown(
        "Ask questions about your data in plain English. "
        "The agent will ask clarifying questions, create an analysis plan, "
        "and generate SQL queries to answer your questions."
    )

    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(
            label="Data Analysis Agent",
            height=400,
            type="messages",
            elem_classes=["chatbot"]
        )

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Ask a question about your data... (e.g., 'Show me total sales by region last quarter')",
                scale=4
            )
            go_button = gr.Button("Go!", variant="primary", scale=1)

    # Clarifications section (shown when agent asks questions)
    with gr.Group(visible=False) as clarification_section:
        gr.Markdown("### Clarifying Questions")
        clarifications = gr.Textbox(
            label="Your Answers",
            placeholder="Please answer the clarifying questions above to help me analyze your data request...",
            lines=4
        )
        submit_clarifications = gr.Button("Submit Answers", variant="secondary")

    # Analysis details section
    with gr.Accordion("Analysis Details", open=False):
        plan_display = gr.Textbox(
            label="Analysis Plan",
            lines=6,
            elem_classes=["analysis-plan"]
        )
        sql_display = gr.Textbox(
            label="SQL Query",
            lines=4,
            elem_classes=["sql-preview"]
        )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        clear_button = gr.Button("Clear")

    # Event handlers
    ui.load(setup, [], [sidekick])

    # Submit message
    message.submit(
        process_message,
        [sidekick, message, chatbot],
        [chatbot, sidekick]
    ).then(
        lambda: ("", None)  # Clear input after submit
    )

    go_button.click(
        process_message,
        [sidekick, message, chatbot],
        [chatbot, sidekick]
    ).then(
        lambda: ("", None)  # Clear input after submit
    )

    # Submit clarifications
    submit_clarifications.click(
        process_with_clarification,
        [sidekick, message, clarifications, chatbot],
        [chatbot, sidekick]
    ).then(
        lambda: ("", "", None)  # Clear inputs
    )

    # Reset
    reset_button.click(
        reset,
        [],
        [message, chatbot, sidekick]
    )

    # Clear
    clear_button.click(
        lambda: ("", None, []),
        [],
        [message, clarifications, chatbot]
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
