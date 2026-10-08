from agents import Agent, Runner
from context import TWIN_SYSTEM_PROMPT
from tools import TWIN_TOOLS
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

twin = Agent(name="Digital Twin", model=MODEL_NAME, instructions=TWIN_SYSTEM_PROMPT, tools=TWIN_TOOLS)

async def chat(message, history):
    input_items = []
    for turn in history:
        role = turn.get("role")
        content = turn.get("content")

        if role not in ("user", "assistant"):
            continue

        if isinstance(content, list):
            content = "\n".join(
                block["text"]
                for block in content
                if isinstance(block, dict)
                and isinstance(block.get("text"), str)
            )

        if isinstance(content, str):
            input_items.append({"role": role, "content": content})

    input_items.append({"role": "user", "content": message})

    result = await Runner.run(twin, input_items)
    return result.final_output

if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())
