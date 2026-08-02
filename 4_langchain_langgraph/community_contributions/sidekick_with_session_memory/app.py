import gradio as gr
import sessionDatabase
from sidekick import Sidekick

async def setup():
    sidekick = Sidekick()
    await sidekick.setup()

    sessions = get_sessions()
    return sidekick, sessions

def get_sessions():
    sessionDatabase.init_db()
    saved_sessions = sessionDatabase.get_sessions()
    sessions = [(row[1], row[0]) for row in saved_sessions]
    return gr.update(choices=sessions)

def set_session(session_id, sidekick):
    
    sidekick.set_sidekick_id(session_id)

    session_row = sessionDatabase.get_session_by_id(session_id)
    session_name = session_row[1] if session_row else ""
    return session_name, sidekick

def save_session(session_name, sidekick):

    sessionDatabase.add_session(sidekick.sidekick_id, session_name)

    sessions = get_sessions()
    return session_name, sessions

async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, "", None


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


def rename_session(new_name, sidekick_state):
    return new_name, sidekick_state


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)


    with gr.Row():
        session_dropdown = gr.Dropdown(label="Select saved session", choices=[], interactive=True)
    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row(equal_height=True):
            session_name_input = gr.Textbox(show_label=False, placeholder="Enter session name", scale=4)
            save_session_button = gr.Button("Save session", scale=0, variant="primary")
            clear_session_button = gr.Button("Clear session", scale=0, variant="stop")
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick, session_dropdown])

    session_dropdown.change(
        fn=set_session, inputs=[session_dropdown, sidekick], outputs=[session_name_input, sidekick])

    session_name_input.submit(
        fn=rename_session, inputs=[session_name_input, sidekick]
    )

    save_session_button.click(
        fn=save_session, inputs=[session_name_input, sidekick], outputs=[session_name_input, session_dropdown]
    )

    clear_session_button.click(
        fn=lambda: ("", None), inputs=[], outputs=[session_name_input, session_dropdown]
    )

    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick, session_name_input, session_dropdown])


ui.launch(inbrowser=True)
