import os

import gradio as gr
from dotenv import load_dotenv

from pipeline import TechEval

load_dotenv(override=True)


async def evaluate(question: str):
    if not question:
        yield "type something first"
        return

    parts = []
    async for chunk in TechEval().run(question):
        if chunk.startswith("[status] "):
            parts.append(chunk.removeprefix("[status] "))
        else:
            parts.append("---\n\n## Analysis\n\n" + chunk)
        yield "\n\n".join(parts)


with gr.Blocks(
    theme=gr.themes.Default(primary_hue="emerald"),
    title="tech eval",
) as ui:
    gr.Markdown(
        "# tech stack scout\n\n"
        "Describe what you're evalauting: a framework, library, tool or architecture pattern. "
        "Agents research real-world experiences and give you an honest take."
    )
    q = gr.Textbox(
        label="what are you evaluating?",
        placeholder="e.g. Should we adopt htmx instead of React for internal dashboards?",
        lines=2,
    )
    go = gr.Button("evaluate", variant="primary")
    out = gr.Markdown(label="results")

    go.click(fn=evaluate, inputs=q, outputs=out)
    q.submit(fn=evaluate, inputs=q, outputs=out)

if __name__ == "__main__":
    ui.launch(inbrowser=True)
