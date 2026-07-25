import gradio as gr
from sidekick import Sidekick

async def setup():
    sidekick = Sidekick(user_id="default")
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history):
    """
    Run one superstep and return updated chat history plus any pending question.

    If the agent asked a clarifying question:
      - the question is shown in the clarification_box
      - the answer textbox becomes visible and focused
    Otherwise the clarification row stays hidden.
    """
    if not message or not message.strip():
        return history, sidekick, gr.update(), gr.update(visible=False), gr.update(visible=False)

    history, pending_question = await sidekick.run_superstep(
        message, success_criteria, history
    )

    if pending_question:
        return (
            history,
            sidekick,
            gr.update(value=pending_question),
            gr.update(visible=True),
            gr.update(visible=True, value=""),
        )
    else:
        return (
            history,
            sidekick,
            gr.update(value=""),
            gr.update(visible=False),
            gr.update(visible=False, value=""),
        )


async def submit_clarification(sidekick, clarification_answer, success_criteria, history):
    """
    The user has typed an answer to the agent's clarifying question.
    Feed it back as a new user message so the agent can continue.
    """
    if not clarification_answer or not clarification_answer.strip():
        return history, sidekick, gr.update(), gr.update(visible=True), gr.update(visible=True)

    return await process_message(sidekick, clarification_answer, success_criteria, history)


async def reset():
    new_sidekick = Sidekick(user_id="default")
    await new_sidekick.setup()
    return (
        "",
        "",
        None,
        new_sidekick,
        gr.update(value=""),
        gr.update(visible=False),
        gr.update(visible=False, value=""),
    )


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## 🤖 Sidekick — Personal Co-Worker")
    sidekick_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=400, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Your request to the Sidekick",
                scale=4,
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria (optional) — e.g. 'Return a bullet-point summary under 200 words'",
                scale=4,
            )

    with gr.Group(visible=False) as clarification_row:
        gr.Markdown("### 🤔 The agent has a clarifying question for you:")
        clarification_box = gr.Textbox(
            label="Agent's question",
            interactive=False,
            lines=2,
        )
        with gr.Row():
            clarification_answer = gr.Textbox(
                show_label=False,
                placeholder="Type your answer here and press Enter or click 'Answer'",
                scale=4,
                visible=False,
            )
            answer_button = gr.Button("Answer ↩", variant="primary", scale=1, visible=False)

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    OUTPUTS = [chatbot, sidekick_state, clarification_box, clarification_row, clarification_answer]

    ui.load(setup, [], [sidekick_state])

    message.submit(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        OUTPUTS,
    )
    
    go_button.click(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        OUTPUTS,
    )

    success_criteria.submit(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        OUTPUTS,
    )

    clarification_answer.submit(
        submit_clarification,
        [sidekick_state, clarification_answer, success_criteria, chatbot],
        OUTPUTS,
    )

    answer_button.click(
        submit_clarification,
        [sidekick_state, clarification_answer, success_criteria, chatbot],
        OUTPUTS,
    )

    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, sidekick_state,
         clarification_box, clarification_row, clarification_answer],
    )

ui.launch(inbrowser=True)