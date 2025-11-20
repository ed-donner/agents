import gradio as gr
from sidekick import Sidekick


async def setup(request: gr.Request):
    """
    Setup Sidekick with username from Gradio authentication.
    Uses gr.Request to access the logged-in username.
    """
    username = request.username if hasattr(request, 'username') and request.username else None
    sidekick = Sidekick(username=username)
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    """
    Process user message through Sidekick.
    The username is already stored in the sidekick instance from setup.
    """
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset(request: gr.Request):
    """
    Reset Sidekick while maintaining the same username for persistent memory.
    """
    username = request.username if hasattr(request, 'username') and request.username else None
    new_sidekick = Sidekick(username=username)
    await new_sidekick.setup()
    return "", "", None, new_sidekick


async def show_history(sidekick):
    """
    Load and display conversation history from the database.
    """
    if not sidekick:
        return [{"role": "assistant", "content": "No active session. Please refresh the page."}]
    
    history = await sidekick.get_history()
    if not history:
        return [{"role": "assistant", "content": "No conversation history found for this user."}]
    return history


async def clear_history(sidekick):
    """
    Clear all conversation history for the current user from the database.
    """
    if not sidekick:
        return [{"role": "assistant", "content": "No active session. Please refresh the page."}], sidekick
    
    result_msg = await sidekick.clear_history()
    return [{"role": "assistant", "content": result_msg}], sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    gr.Markdown("**Note:** Login with your username to enable persistent memory across sessions!")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )
    with gr.Row():
        show_history_button = gr.Button("📜 Show History", variant="secondary")
        clear_history_button = gr.Button("🗑️ Clear History", variant="stop")
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])
    show_history_button.click(show_history, [sidekick], [chatbot])
    clear_history_button.click(clear_history, [sidekick], [chatbot, sidekick])


# Launch with authentication - users must login with username/password
# The username will be used as the thread_id for SQLite memory persistence
ui.launch(
    inbrowser=True,
    auth=[("javi", "password123"), ("alice", "alice123"), ("bob", "bob123")]  # Example users
)
