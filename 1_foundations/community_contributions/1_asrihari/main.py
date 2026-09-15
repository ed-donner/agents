from openai import OpenAI
import gradio as gr
OLLAMA_BASE_URL = "http://localhost:11434/v1"
from context import MED_SYSTEM_PROMPT
from styles import CSS, JS, EXAMPLES
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
model_name = "medgemma:latest"


system_message = [
    {"role": "system", "content": MED_SYSTEM_PROMPT}
]

def chat(message, history):
    messages = system_message + history + [{"role": "user", "content": message}]
    response = ollama.chat.completions.create(model=model_name, messages=messages)
    return response.choices[0].message.content

if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="MedAssist",
        description="You are MedAssist, an AI Healthcare Assistant powered by MedGemma.",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())