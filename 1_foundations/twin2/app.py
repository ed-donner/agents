from context import TWIN_SYSTEM_PROMPT, TWIN_NAME
from tools import tools
from styles import CSS, build_js, EXAMPLES
from dotenv import load_dotenv
import gradio as gr
from agents import Agent, Runner

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

agent = Agent(name="Digital Twin", instructions=TWIN_SYSTEM_PROMPT, model=MODEL_NAME, tools=tools)

async def chat(message, history):
    messages = [{"role": m["role"], "content": m["content"]} for m in history] + [{"role": "user", "content": message}]
    result = await Runner.run(agent, messages)
    return result.final_output


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title=f"{TWIN_NAME} — Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=build_js(TWIN_NAME), theme=gr.themes.Base())
