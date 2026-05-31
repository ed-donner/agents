import gradio as gr
import asyncio
from meal_agent import run_agent


conversation_history: list[dict] = []


async def chat(message: str, chat_history: list):
    global conversation_history
    response = await run_agent(message, conversation_history)
    conversation_history.append({"role": "user", "content": message})
    conversation_history.append({"role": "assistant", "content": response})
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})
    return "", chat_history


def reset_chat():
    global conversation_history
    conversation_history = []
    return "", []


with gr.Blocks(title="Meal Planner", theme=gr.themes.Default(primary_hue="orange")) as ui:
    gr.Markdown("## Recipe Finder & Meal Planner")
    gr.Markdown(
        "Search recipes by keyword, cuisine, or ingredient. "
        "Plan your weekly meals and generate a shopping list — all powered by MCP."
    )

    chatbot = gr.Chatbot(label="Meal Planner", height=450, type="messages")

    with gr.Row():
        message = gr.Textbox(
            show_label=False,
            placeholder="e.g. Plan me 5 dinners for next week — I like Italian and Japanese food",
            scale=4,
        )
        go_button = gr.Button("Send", variant="primary", scale=1)

    with gr.Row():
        reset_button = gr.Button("New Conversation", variant="stop")

    message.submit(chat, [message, chatbot], [message, chatbot])
    go_button.click(chat, [message, chatbot], [message, chatbot])
    reset_button.click(reset_chat, [], [message, chatbot])

ui.launch(inbrowser=True)
