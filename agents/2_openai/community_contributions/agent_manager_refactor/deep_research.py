import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from manager_agent import manager_agent

load_dotenv(override=True)


async def run_chat(user_message: str, chat_history: list):
    chat_history.append({"role": "user", "content": user_message})

    chat_history.append({"role": "assistant", "content": "Pensando..."})
    yield chat_history, ""

    messages = [{"role": message["role"], "content": message["content"]} for message in chat_history[:-1]]

    result = await Runner.run(
        manager_agent,
        messages,
    )

    chat_history[-1] = {"role": "assistant", "content": result.final_output}
    yield chat_history, ""


with gr.Blocks() as ui:
    chat = gr.Chatbot(type="messages", label="Agente de investigación profunda")
    chat_history = gr.State([])
    
    txt = gr.Textbox(placeholder="Escribe aquí…", show_label=False)
    btn = gr.Button("Enviar")
    
    btn.click(
        fn=run_chat,
        inputs=[txt, chat_history],
        outputs=[chat, txt],
    )
    txt.submit(
        fn=run_chat,
        inputs=[txt, chat_history],
        outputs=[chat, txt],
    )

ui.launch(inbrowser=True)

