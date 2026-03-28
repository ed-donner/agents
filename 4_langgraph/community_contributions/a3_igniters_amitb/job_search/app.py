import gradio as gr
from job_search.main import JobsSearchAssistant


async def setup():
    job_search_assistant = JobsSearchAssistant()
    await job_search_assistant.setup()
    return job_search_assistant


async def process_message(job_search_assistant: JobsSearchAssistant, message,
                          success_criteria: str, history: list[dict]):
    results = await job_search_assistant.run_superstep(message, success_criteria, history)
    return results, job_search_assistant


async def reset():
    new_job_search = JobsSearchAssistant()
    await new_job_search.setup()
    return "", "", None, new_job_search


def free_resources(job_search_assistant):
    print("Cleaning up")
    try:
        if job_search_assistant:
            job_search_assistant.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Job Search Assistant", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Personal Job Search Assistant")
    job_search_assistant = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Job Search Assistant", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Job Search Assistant")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [job_search_assistant])
    message.submit(
        process_message, [job_search_assistant, message, success_criteria, chatbot], [chatbot, job_search_assistant]
    )
    success_criteria.submit(
        process_message, [job_search_assistant, message, success_criteria, chatbot], [chatbot, job_search_assistant]
    )
    go_button.click(
        process_message, [job_search_assistant, message, success_criteria, chatbot], [chatbot, job_search_assistant]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, job_search_assistant])


ui.launch(inbrowser=True)
