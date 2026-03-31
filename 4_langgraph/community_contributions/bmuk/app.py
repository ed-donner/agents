import gradio as gr
from sidekick import Sidekick


async def setup(username):
    sidekick = Sidekick(sidekick_id=username)
    await sidekick.setup()
    history = await sidekick.get_history()
    return sidekick,history


async def process_message(sidekick, message, success_criteria, history, request: gr.Request):
    if sidekick is None:
            gr.Warning("Sidekick is not initialized. Please wait and try again.")
            sidekick,history = await setup(request.username)
    try:
        results = await sidekick.run_superstep(message, success_criteria, history)
        return results, sidekick
    except Exception as e:
        raise gr.Error(f"An error occurred: {str(e)}")


async def reset(request: gr.Request):
    username = request.username
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", [], new_sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

def authenticate_user(username, password):
    valid_users = {
        "bob": "password123",
        "alice": "securepassword",
    }
    return valid_users.get(username) == password

async def load(request: gr.Request):
    sidekick, history = await setup(request.username)
    return sidekick, history



with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
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
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")
    with gr.Row():
        logout_button = gr.Button("Logout", variant="huggingface",link="/logout")

    ui.load(load, [], [sidekick, chatbot])
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


ui.launch(inbrowser=True,debug=True,auth=authenticate_user)
