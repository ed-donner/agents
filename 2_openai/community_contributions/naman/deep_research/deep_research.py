from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from clarification_agent import ClarifyingQuestions
from research_manager import ResearchManager

load_dotenv(override=True)

CLARIFY_COL_CLASS = "clarify-col"
CUSTOM_CSS = f"""
.{CLARIFY_COL_CLASS} {{
    padding: 1rem 0.8rem;
}}
.header {{
    margin-bottom: 12px;
    text-align: center;
    font-size: 2rem;
    color: var(--primary-color);
}}
"""

NUM_QUESTIONS = 3


async def generate_clarification_questions(query: str) -> list[str]:
    cq = await ResearchManager().get_clarifying_questions(query)
    qs = list(cq.questions)
    if len(qs) < NUM_QUESTIONS:
        qs.extend([""] * (NUM_QUESTIONS - len(qs)))
    return qs[:NUM_QUESTIONS]


async def on_run(query: str):
    if not query or not query.strip():
        return (
            "*Please enter a research topic.*",
            None,
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=""),
        )
    questions = await generate_clarification_questions(query.strip())
    return (
        "Answer the clarifying questions above, then click **Continue**.",
        questions,
        gr.update(visible=True),
        gr.update(value=f"**1.** {questions[0]}"),
        gr.update(value=f"**2.** {questions[1]}"),
        gr.update(value=f"**3.** {questions[2]}"),
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=""),
    )


async def on_continue(
    topic: str,
    questions_state: list[str] | None,
    a1: str,
    a2: str,
    a3: str,
):
    if not topic or not topic.strip():
        yield "*Please enter a research topic.*"
        return
    if not questions_state or len(questions_state) != NUM_QUESTIONS:
        yield "*No clarifying questions loaded. Click **Run** first.*"
        return
    cq = ClarifyingQuestions(questions=list(questions_state))
    answers = [a1 or "", a2 or "", a3 or ""]
    async for chunk in ResearchManager().run(topic.strip(), cq, answers):
        yield chunk


with gr.Blocks(
    theme=gr.themes.Default(primary_hue="indigo"),
    css=CUSTOM_CSS,
    title="Deep Research - Report Generation",
) as ui:
    gr.Markdown("# 🔎 Deep Research", elem_classes=["header"])
    question_state = gr.State(value=None)

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")

    with gr.Group(visible=False) as clarification_group:
        with gr.Row(equal_height=True):
            with gr.Column(elem_classes=[CLARIFY_COL_CLASS]):
                q1_md = gr.Markdown()
                answer1 = gr.Textbox(label="Answer 1", lines=2)
            with gr.Column(elem_classes=[CLARIFY_COL_CLASS]):
                q2_md = gr.Markdown()
                answer2 = gr.Textbox(label="Answer 2", lines=2)
            with gr.Column(elem_classes=[CLARIFY_COL_CLASS]):
                q3_md = gr.Markdown()
                answer3 = gr.Textbox(label="Answer 3", lines=2)
        continue_button = gr.Button("Continue", variant="primary")

    gr.Markdown("---")
    report = gr.Markdown(label="Report")

    run_outputs = [
        report,
        question_state,
        clarification_group,
        q1_md,
        q2_md,
        q3_md,
        answer1,
        answer2,
        answer3,
    ]
    run_button.click(fn=on_run, inputs=query_textbox, outputs=run_outputs)
    query_textbox.submit(fn=on_run, inputs=query_textbox, outputs=run_outputs)

    continue_button.click(
        fn=on_continue,
        inputs=[query_textbox, question_state, answer1, answer2, answer3],
        outputs=report,
    )

_APP_DIR = Path(__file__).resolve().parent

ui.launch(
    inbrowser=True,
    favicon_path=str(_APP_DIR / "favicon.ico"),
)
