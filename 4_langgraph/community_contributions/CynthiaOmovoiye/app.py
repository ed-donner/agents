import uuid

import gradio as gr

from sidekick import Sidekick, make_thread_id


async def initial_setup(username: str):
    sid = str(uuid.uuid4())
    tid = make_thread_id(username, sid)
    sk = Sidekick(thread_id=tid)
    await sk.setup()
    return sk, sid


async def process_message(sidekick, username, session_id, message, success_criteria, history):
    tid = make_thread_id(username, session_id)
    if sidekick is None or getattr(sidekick, "thread_id", None) != tid:
        if sidekick is not None:
            sidekick.cleanup()
        sidekick = Sidekick(thread_id=tid)
        await sidekick.setup()
    results = await sidekick.run_superstep(message, success_criteria, history)
    # Clear only the message box; keep success criteria for follow-up turns (clarification + same task).
    return results, sidekick, ""


async def reset(sidekick, username, session_id: str):
    """Named users: clear SQLite checkpoints for their thread but keep the same thread id. Anonymous: new session id + new sidekick."""
    uname = (username or "").strip()
    if uname:
        tid = make_thread_id(username, session_id)
        if sidekick is None or getattr(sidekick, "thread_id", None) != tid:
            if sidekick is not None:
                sidekick.cleanup()
            sk = Sidekick(thread_id=tid)
            await sk.setup()
        else:
            sk = sidekick
        await sk.clear_thread_checkpoint_async()
        return "", "", None, sk, session_id

    new_session = str(uuid.uuid4())
    if sidekick is not None:
        sidekick.cleanup()
    sk = Sidekick(thread_id=make_thread_id("", new_session))
    await sk.setup()
    return "", "", None, sk, new_session


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    gr.Markdown(
        "Set a **username** to use it as the LangGraph **thread id**: your chat is restored from the database"
        "when you reload the app. **Reset** clears saved checkpoints for that "
        "username and starts a fresh conversation. Leave username empty for an anonymous session "
        "(memory is keyed by a random id until you reset). "
        "The sidekick asks **three clarifying questions one at a time**; each question uses your previous answers."
    )
    sidekick = gr.State(delete_callback=free_resources)
    session_id = gr.State(lambda: str(uuid.uuid4()))

    with gr.Row():
        username = gr.Textbox(
            label="Username (thread id)",
            placeholder="e.g. your name — used for saved memory",
            scale=2,
        )
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

    ui.load(initial_setup, [username], [sidekick, session_id])
    message.submit(
        process_message,
        [sidekick, username, session_id, message, success_criteria, chatbot],
        [chatbot, sidekick, message],
    )
    success_criteria.submit(
        process_message,
        [sidekick, username, session_id, message, success_criteria, chatbot],
        [chatbot, sidekick, message],
    )
    go_button.click(
        process_message,
        [sidekick, username, session_id, message, success_criteria, chatbot],
        [chatbot, sidekick, message],
    )
    reset_button.click(
        reset,
        [sidekick, username, session_id],
        [message, success_criteria, chatbot, sidekick, session_id],
    )


ui.launch(inbrowser=True)
