import os
from pathlib import Path

import gradio as gr
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI


def _load_env_files():
    app_dir = Path(__file__).resolve().parent
    repo_env = next((parent / ".env" for parent in app_dir.parents if (parent / ".env").is_file()), None)
    app_env = app_dir / ".env"

    if repo_env:
        load_dotenv(repo_env)
    if app_env.is_file() and app_env != repo_env:
        load_dotenv(app_env, override=True)


_load_env_files()

from research_manager import ResearchManager

manager = ResearchManager()


async def generate_questions(query: str):
    if not query.strip():
        gr.Warning("Please enter a research query first.")
        return [gr.update()] * 8

    questions = await manager.get_clarifying_questions(query)
    return (
        gr.update(value=questions[0], visible=True),
        gr.update(value="", visible=True),
        gr.update(value=questions[1], visible=True),
        gr.update(value="", visible=True),
        gr.update(value=questions[2], visible=True),
        gr.update(value="", visible=True),
        gr.update(visible=True),
        gr.update(value="Clarifying questions generated. Answer all three, then run research."),
    )


async def research(query: str, q1: str, a1: str, q2: str, a2: str, q3: str, a3: str):
    answers = [a1, a2, a3]
    if not query.strip():
        gr.Warning("Please enter a research query first.")
        yield "", ""
        return

    if not all(answer.strip() for answer in answers):
        gr.Warning("Please answer all three clarifying questions.")
        yield "", ""
        return

    qa_pairs = [(q1, a1), (q2, a2), (q3, a3)]
    async for status_text, report_markdown in manager.run_research(query, qa_pairs):
        yield status_text, report_markdown


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Igniters Deep Research Agent")
    gr.Markdown(
        "OpenRouter-backed deep research with a clarifier step, autonomous research rounds, "
        "coverage evaluation, and a final report."
    )

    gr.Markdown("### Step 1: Enter a research query")
    query_input = gr.Textbox(
        label="Research Query",
        placeholder="What topic would you like to research?",
        lines=2,
    )
    clarify_button = gr.Button("Generate Clarifying Questions", variant="secondary")

    gr.Markdown("### Step 2: Answer the clarifying questions")
    q1 = gr.Textbox(label="Question 1", interactive=False, visible=False)
    a1 = gr.Textbox(label="Your Answer", placeholder="Type your answer...", visible=False)
    q2 = gr.Textbox(label="Question 2", interactive=False, visible=False)
    a2 = gr.Textbox(label="Your Answer", placeholder="Type your answer...", visible=False)
    q3 = gr.Textbox(label="Question 3", interactive=False, visible=False)
    a3 = gr.Textbox(label="Your Answer", placeholder="Type your answer...", visible=False)
    research_button = gr.Button("Run Deep Research", variant="primary", visible=False)

    gr.Markdown("### Step 3: Review the report")
    status_output = gr.Markdown()
    report_output = gr.Markdown()

    clarify_button.click(
        fn=generate_questions,
        inputs=query_input,
        outputs=[q1, a1, q2, a2, q3, a3, research_button, status_output],
    )

    research_button.click(
        fn=research,
        inputs=[query_input, q1, a1, q2, a2, q3, a3],
        outputs=[status_output, report_output],
    )

ui.queue()


def create_app() -> FastAPI:
    host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    app = FastAPI()
    return gr.mount_gradio_app(app, ui, path="/", server_name=host, server_port=port)


def launch_app():
    host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    uvicorn.run(
        create_app(),
        host=host,
        port=port,
        loop="asyncio",
        http="h11",
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    launch_app()
