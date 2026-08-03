import re

import gradio as gr
from agents import gen_trace_id
from dotenv import load_dotenv
from research_manager import ResearchManager
from clarify_agent import NUMBER_OF_QUESTIONS

load_dotenv(override=True)


def parse_clarifying_answers(answers_text: str) -> list[str]:
    answers: list[str] = []
    for line in answers_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^\d+[\.)]\s*", "", line)
        if line:
            answers.append(line)
    return answers


async def start_research(query: str):
    """Start the research process from scratch."""
    trace_id = gen_trace_id()
    status_lines: list[str] = []

    async for event in ResearchManager().run(query, history=[], trace_id=trace_id):
        if event["type"] == "status":
            status_lines.append(f"*{event['message']}*")
            yield (
                "\n\n".join(status_lines),
                gr.update(visible=False),
                gr.update(visible=False),
                query,
                trace_id,
                None,
                [],
            )

        elif event["type"] == "clarification":
            yield (
                f"**Question 1/{NUMBER_OF_QUESTIONS}:** {event['question']}",
                gr.update(visible=True, value=""),
                gr.update(visible=True),
                query,
                trace_id,
                event["question"],
                [],
            )
            return

        elif event["type"] == "report":
            yield (
                event["content"],
                gr.update(visible=False),
                gr.update(visible=False),
                query,
                trace_id,
                None,
                [],
            )


async def continue_research(
    query: str,
    answer_text: str,
    history: list[dict],
    current_question: str | None,
    trace_id: str | None,
):
    """Continue research after the user answers a clarifying question."""
    answer = answer_text.strip() if answer_text else ""
    if not answer:
        yield (
            "Please provide an answer before continuing.",
            gr.update(visible=True),
            gr.update(visible=True),
            current_question,
            history,
        )
        return

    new_history = (history or []) + [{"question": current_question, "answer": answer}]
    status_lines: list[str] = []

    async for event in ResearchManager().run(query, history=new_history, trace_id=trace_id):
        if event["type"] == "status":
            status_lines.append(f"*{event['message']}*")
            yield (
                "\n\n".join(status_lines),
                gr.update(visible=False),
                gr.update(visible=False),
                current_question,
                new_history,
            )

        elif event["type"] == "clarification":
            q_num = len(new_history) + 1
            yield (
                f"**Question {q_num}/{NUMBER_OF_QUESTIONS}:** {event['question']}",
                gr.update(visible=True, value=""),
                gr.update(visible=True),
                event["question"],
                new_history,
            )
            return

        elif event["type"] == "report":
            yield (
                event["content"],
                gr.update(visible=False),
                gr.update(visible=False),
                current_question,
                new_history,
            )


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    clarifying_answers = gr.Textbox(
        label="Your answer",
        lines=4,
        visible=False,
        placeholder="Your answer here...",
    )
    continue_button = gr.Button("Continue", variant="primary", visible=False)
    query_state = gr.State()
    trace_state = gr.State()
    current_question_state = gr.State()
    history_state = gr.State([])

    shared_outputs = [report, clarifying_answers, continue_button, query_state, trace_state, current_question_state, history_state]

    run_button.click(
        fn=start_research,
        inputs=[query_textbox],
        outputs=shared_outputs,
    )
    query_textbox.submit(
        fn=start_research,
        inputs=[query_textbox],
        outputs=shared_outputs,
    )
    continue_button.click(
        fn=continue_research,
        inputs=[query_state, clarifying_answers, history_state, current_question_state, trace_state],
        outputs=[report, clarifying_answers, continue_button, current_question_state, history_state],
    )

ui.launch(inbrowser=True)
