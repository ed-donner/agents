import os


import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

SYSTEM = """You are a precise summarizer. You:
- Preserve important facts, names, dates, and numbers when present.
- Do not invent content that is not implied by the source.
- Match the user's requested length and format.
"""

def summarize(
    text: str,
    length: str,
    output_format: str,
    model: str,
) -> str:
    text = (text or "").strip()
    if not text:
        return "Paste some text to summarize."
    if not model:
        model = "google/gemini-2.0-flash-001"
    length_hints = {
        "Short (1-2 sentences)": "1-2 sentences.",
        "Medium (one short paragraph)": "One short paragraph, roughly 80-120 words.",
        "Long (several paragraphs)": "Several short paragraphs covering all major themes.",
    }
    format_hints = {
        "Prose": "Write flowing prose.",
        "Bullet points": "Use bullet points; group related ideas.",
        "TL;DR + detail": "Start with a one-line TL;DR, then a slightly longer explanation.",
    }
    user_msg = (
        f"Length: {length_hints.get(length, length_hints['Medium (one short paragraph)'])}\n"
        f"Format: {format_hints.get(output_format, format_hints['Prose'])}\n\n"
        f"--- Source text ---\n{text}"
    )
    print(f"Using model: {model}")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()
def ui():
    with gr.Blocks(title="Text summarizer") as demo:
        gr.Markdown("Multi-Model Text summarizer using OpenRouter-")
        inp = gr.Textbox(
            label="Text to summarize",
            lines=14,
            placeholder="Paste an article, notes, email thread, etc.",
        )
        with gr.Row():
            length = gr.Dropdown(
                choices=[
                    "Short (1-2 sentences)",
                    "Medium (one short paragraph)",
                    "Long (several paragraphs)",
                ],
                value="Medium (one short paragraph)",
                label="Length",
            )
            fmt = gr.Dropdown(
                choices=["Prose", "Bullet points", "TL;DR + detail"],
                value="Prose",
                label="Format",
            )
            model = gr.Dropdown(
                choices=["google/gemini-2.0-flash-001", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "deepseek/deepseek-chat-v2.5"],
                value="google/gemini-2.0-flash-001",
                label="Model",
            )
        btn = gr.Button("Summarize", variant="primary")
        out = gr.Textbox(label="Summary", lines=12)
        btn.click(fn=summarize, inputs=[inp, length, fmt, model], outputs=[out])
    return demo
if __name__ == "__main__":
    ui().launch()