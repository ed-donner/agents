import gradio as gr
from sidekick import Sidekick


async def setup(request: gr.Request):
    username = request.username if request.username else "anonymous"
    sidekick = Sidekick(user_id=username)
    await sidekick.setup()
    return sidekick, f"Welcome, {username}!"


async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset(request: gr.Request):
    username = request.username if request.username else "anonymous"
    new_sidekick = Sidekick(user_id=username)
    await new_sidekick.setup()
    return "", "", None, new_sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


def authenticate(username: str, password: str) -> bool:
    """Simple authentication function. You can customize this with your own logic."""
    # Hardcoded users for now
    valid_users = {
        "test": "test",
        "admin": "admin",
    }
    return valid_users.get(username) == password


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    
    sidekick = gr.State(delete_callback=free_resources)
    welcome_msg = gr.Textbox(label="Status", interactive=False, value="Loading...")

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
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick, welcome_msg])
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


ui.launch(inbrowser=True, auth=authenticate)
