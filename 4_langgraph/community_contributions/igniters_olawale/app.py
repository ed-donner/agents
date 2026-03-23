import gradio as gr
from clarify import generate_clarifying_questions
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(
    sidekick, message, success_criteria, history, user_chat_content=None
):
    results = await sidekick.run_superstep(
        message, success_criteria, history, user_chat_content=user_chat_content
    )
    return results, sidekick


async def on_enter(
    sidekick,
    message,
    success_criteria,
    history,
    phase,
    task_snapshot,
    questions_snapshot,
):
    if not message or not str(message).strip():
        raise gr.Error("Type a message in the chat box.")

    if phase == "await_task":
        q1, q2, q3 = await generate_clarifying_questions(message.strip())
        user_msg = {"role": "user", "content": message.strip()}
        assistant_msg = {
            "role": "assistant",
            "content": (
                "Before I continue, answer these three questions in your next message:\n\n"
                f"1. {q1}\n\n2. {q2}\n\n3. {q3}"
            ),
        }
        base = list(history) if history else []
        new_hist = base + [user_msg, assistant_msg]
        return (
            gr.update(value=""),
            new_hist,
            sidekick,
            "await_answers",
            message.strip(),
            (q1, q2, q3),
        )

    full_message = (
        f"User task:\n{task_snapshot}\n\n"
        f"Clarifying questions that were asked:\n"
        f"1. {questions_snapshot[0]}\n"
        f"2. {questions_snapshot[1]}\n"
        f"3. {questions_snapshot[2]}\n\n"
        f"User's answers:\n{message.strip()}\n"
    )
    results, sk = await process_message(
        sidekick,
        full_message,
        success_criteria,
        list(history or []),
        user_chat_content=message.strip(),
    )
    return (
        gr.update(value=""),
        results,
        sk,
        "await_task",
        "",
        None,
    )


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, "await_task", None, ""


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)
    phase_state = gr.State("await_task")
    questions_state = gr.State(None)
    task_state = gr.State("")

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=360, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="Your request; after the three questions appear, reply here with your answers",
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Send", variant="primary")

    ui.load(setup, [], [sidekick])

    go_button.click(
        on_enter,
        [sidekick, message, success_criteria, chatbot, phase_state, task_state, questions_state],
        [message, chatbot, sidekick, phase_state, task_state, questions_state],
    )
    message.submit(
        on_enter,
        [sidekick, message, success_criteria, chatbot, phase_state, task_state, questions_state],
        [message, chatbot, sidekick, phase_state, task_state, questions_state],
    )

    reset_button.click(
        reset,
        [],
        [
            message,
            success_criteria,
            chatbot,
            sidekick,
            phase_state,
            questions_state,
            task_state,
        ],
    )


ui.launch(inbrowser=True)
