import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
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



with gr.Blocks(title='Event Planner', theme=gr.themes.Soft()) as ui:
    gr.Markdown('## Personal Event Planner')
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label = 'Event Planner', height=300, type='messages')
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder='Start your event request; Please provide the exact date.')
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False,
            placeholder='What is important for you')

    with gr.Row():
        reset_button = gr.Button('Reset', variant='stop')
        go_button = gr.Button('Plan my Event', variant='primary')


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


ui.launch(inbrowser=True)