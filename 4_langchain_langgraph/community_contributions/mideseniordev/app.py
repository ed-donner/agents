import gradio as gr

from sidekick import Sidekick


def setup() -> Sidekick:
    return Sidekick()


def chat(
    sidekick: Sidekick,
    message: str,
    success_criteria: str,
    history: list[dict[str, str]],
):
    history = history or []
    updated_history, plan, feedback, card = sidekick.run_turn(
        message=message,
        success_criteria=success_criteria,
        chat_history=history,
    )
    return updated_history, plan, feedback, card, sidekick, ""


def reset() -> tuple[str, list[dict[str, str]], str, str, str, Sidekick]:
    fresh = Sidekick()
    return "", [], "", "", "", fresh


with gr.Blocks(title="Action-Card Sidekick", theme=gr.themes.Soft()) as app:
    gr.Markdown("## Action-Card Sidekick (LangGraph)")
    gr.Markdown(
        "Unique add-on: after solving your request, it generates a reusable Action Card "
        "with checklist, risks, and next prompt."
    )

    sidekick_state = gr.State()

    chatbot = gr.Chatbot(type="messages", height=380, label="Conversation")
    message = gr.Textbox(label="Message", placeholder="Ask your sidekick for help...")
    success = gr.Textbox(
        label="Success criteria",
        placeholder="Example: include steps, practical examples, and trade-offs.",
    )

    with gr.Row():
        send_btn = gr.Button("Send", variant="primary")
        reset_btn = gr.Button("Reset", variant="stop")

    with gr.Row():
        plan_box = gr.Markdown(label="Plan")
        feedback_box = gr.Markdown(label="Evaluator feedback")
    card_box = gr.Markdown(label="Action Card")

    app.load(setup, [], [sidekick_state])
    send_btn.click(
        chat,
        [sidekick_state, message, success, chatbot],
        [chatbot, plan_box, feedback_box, card_box, sidekick_state, message],
    )
    message.submit(
        chat,
        [sidekick_state, message, success, chatbot],
        [chatbot, plan_box, feedback_box, card_box, sidekick_state, message],
    )
    reset_btn.click(
        reset,
        [],
        [message, chatbot, plan_box, feedback_box, card_box, sidekick_state],
    )


if __name__ == "__main__":
    app.launch(inbrowser=True)
