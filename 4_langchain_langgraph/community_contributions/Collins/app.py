import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    results, questions = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick, questions, gr.update(visible=bool(questions))


async def submit_answers(sidekick, a1, a2, a3, questions, message, success_criteria, history):
    results, _ = await sidekick.run_superstep(
        message, success_criteria, history, clarifying_answers=[a1, a2, a3]
    )
    return results, sidekick, [], gr.update(visible=False)


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, [], gr.update(visible=False)


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick  = gr.State(delete_callback=free_resources)
    questions = gr.State([])

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="What are your success criteria?")

    with gr.Group(visible=False) as answer_panel:
        gr.Markdown("### Answer Sidekick's 3 questions to continue")
        answer1 = gr.Textbox(label="Answer 1")
        answer2 = gr.Textbox(label="Answer 2")
        answer3 = gr.Textbox(label="Answer 3")
        submit_btn = gr.Button("Submit Answers", variant="primary")

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button    = gr.Button("Go!",   variant="primary")

    ui.load(setup, [], [sidekick])

    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick, questions, answer_panel])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick, questions, answer_panel])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick, questions, answer_panel])

    submit_btn.click(submit_answers, [sidekick, answer1, answer2, answer3, questions, message, success_criteria, chatbot], [chatbot, sidekick, questions, answer_panel])

    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick, questions, answer_panel])

ui.launch(inbrowser=True)

if __name__ == "__main__":
    ui.launch(inbrowser=True)