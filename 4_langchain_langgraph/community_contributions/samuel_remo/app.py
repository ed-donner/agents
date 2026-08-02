import gradio as gr
from sidekick import Sidekick
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv(override=True)


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


async def generate_clarifications(message, success_criteria):
    llm = ChatOpenAI(model="gpt-4o-mini")
    messages = [
        SystemMessage(
            content="You are a helpful assistant. Generate exactly 3 concise clarification questions "
            "to better understand the user's request before acting on it. "
            "Format them as a numbered list: 1. ... 2. ... 3. ..."
        ),
        HumanMessage(
            content=f"User request: {message}\nSuccess criteria: {success_criteria}"
        ),
    ]
    response = llm.invoke(messages)
    return response.content


async def handle_go(sidekick, message, success_criteria, history, in_clarification, original_request):
    if not message.strip():
        return history, sidekick, in_clarification, original_request, message

    if not in_clarification:
        questions = await generate_clarifications(message, success_criteria)
        user_msg = {"role": "user", "content": message}
        assistant_msg = {
            "role": "assistant",
            "content": (
                "Before I get started, I have 3 clarification questions:\n\n"
                f"{questions}\n\n"
                "Please answer these questions and click **Go!** again."
            ),
        }
        return history + [user_msg, assistant_msg], sidekick, True, message, ""
    else:
        enriched_message = (
            f"{original_request}\n\n"
            f"Additional context (answers to clarification questions):\n{message}"
        )
        results = await sidekick.run_superstep(enriched_message, success_criteria, history)
        return results, sidekick, False, "", ""


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, False, ""


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)
    in_clarification = gr.State(False)
    original_request = gr.State("")

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success criteria?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    inputs = [sidekick, message, success_criteria, chatbot, in_clarification, original_request]
    outputs = [chatbot, sidekick, in_clarification, original_request, message]

    ui.load(setup, [], [sidekick])
    message.submit(handle_go, inputs, outputs)
    success_criteria.submit(handle_go, inputs, outputs)
    go_button.click(handle_go, inputs, outputs)
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick, in_clarification, original_request])


ui.launch(inbrowser=True)
