import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    """
    sidekick: Sidekick instance (state)
    message: current user input (string)
    success_criteria: text from the success criteria box (string)
    history: current chatbot history (list of messages)
    """
    results = await sidekick.run_superstep(message, success_criteria, history)
    # Return:
    #   - updated chatbot history
    #   - updated sidekick state
    #   - empty string to clear the message box
    return results, sidekick, ""


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    # Clear message, clear success_criteria, clear chat history, reset sidekick
    return "", "", None, new_sidekick


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
        """
This Sidekick **always starts** by asking you exactly **three clarifying questions** (Q1–Q3).

**How to use it:**
1. Type your **initial request** in the Message box and press Enter or click **Go!**.
2. Sidekick will reply with `Q1: ...`, `Q2: ...`, `Q3: ...`.
3. Type your **answers to those questions in the *same* Message box** and press **Go!** again.
4. Sidekick will then do the work according to your Success Criteria.
        """
    )

    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Type your request or your answers to Q1–Q3 here, then press Enter or Go!"
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Optional: How will you judge success? (kept across turns unless you change it)"
            )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    # Initialize Sidekick instance when the UI loads
    ui.load(setup, [], [sidekick])

    # When user hits Enter in the message box
    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, message],   # also clears the message box
    )

    # When user clicks Go!
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, message],   # also clears the message box
    )

    # We no longer submit on pressing Enter inside success_criteria.
    # User can edit success_criteria any time; it will be used on the next Go! call.

    # Reset everything
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])


ui.launch(inbrowser=True)
