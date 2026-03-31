import gradio as gr
from applicant import Applicant


async def setup():
    applicant = Applicant(
        username="Denis Gathondu",
        no_of_postings=10,
        model="gpt-4o-mini",
    )
    await applicant.setup()
    return applicant


async def process_message(applicant, message, job_posting_url, history):
    results = await applicant.run_superstep(message, job_posting_url, history)
    return results, applicant


async def reset():
    new_applicant = Applicant(
        username="Denis Gathondu",
        no_of_postings=10,
        model="gpt-4o-mini",
    )
    await new_applicant.setup()
    return "", "", None, new_applicant


def free_resources(applicant):
    print("Cleaning up")
    try:
        if applicant:
            applicant.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Applicant", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("##  Personal Application Tracker")
    applicant = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Applicant", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False, placeholder="Your request to the Applicant"
            )
        with gr.Row():
            job_posting_url = gr.Textbox(
                show_label=False, placeholder="What is the job posting url?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [applicant])
    message.submit(
        process_message,
        [applicant, message, job_posting_url, chatbot],
        [chatbot, applicant],
    )
    job_posting_url.submit(
        process_message,
        [applicant, message, job_posting_url, chatbot],
        [chatbot, applicant],
    )
    go_button.click(
        process_message,
        [applicant, message, job_posting_url, chatbot],
        [chatbot, applicant],
    )
    reset_button.click(reset, [], [message, job_posting_url, chatbot, applicant])


ui.launch(inbrowser=True)
