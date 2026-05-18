from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root so OPENROUTER_* are set when running from this folder
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_repo_root / ".env", override=True)
load_dotenv(override=True)  # then cwd so local .env overrides

from agents import Runner, trace, gen_trace_id, set_tracing_disabled
from clarifier_agent import clarifier_agent, ClarifyingQuestions
from manager_agent import manager_agent

import gradio as gr

set_tracing_disabled(True)


async def get_clarifying_questions(query: str):
    if not query or not query.strip():
        return "Please enter a research query.", ""
    result = await Runner.run(clarifier_agent, f"Research query: {query}")
    out = result.final_output_as(ClarifyingQuestions)
    numbered = "\n".join(f"{i+1}. {q}" for i, q in enumerate(out.questions))
    return numbered, ""


async def run_research(query: str, clarification_answers: str):
    if not query or not query.strip():
        yield "Please enter a research query.", ""
        return
    if not clarification_answers or not clarification_answers.strip():
        yield "Please answer the 3 clarifying questions above, then run research.", ""
        return

    trace_id = gen_trace_id()
    with trace("Research trace", trace_id=trace_id):
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n\nStarting...", ""
        input_for_manager = (
            f"Research query:\n{query}\n\n"
            f"User's answers to the 3 clarifying questions:\n{clarification_answers}"
        )
        result = await Runner.run(manager_agent, input_for_manager, max_turns=25)
        report = str(result.final_output) if result.final_output else ""
        yield "", report


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    get_questions_btn = gr.Button("Get 3 clarifying questions", variant="secondary")
    questions_out = gr.Textbox(label="Clarifying questions", lines=5, interactive=False)
    answers_box = gr.Textbox(label="Your answers", placeholder="1) ... 2) ... 3) ...", lines=4)
    run_button = gr.Button("Run", variant="primary")
    status = gr.Textbox(label="Status", lines=2, interactive=False)
    report = gr.Markdown(label="Report")

    get_questions_btn.click(fn=get_clarifying_questions, inputs=query_textbox, outputs=[questions_out, report])
    run_button.click(fn=run_research, inputs=[query_textbox, answers_box], outputs=[status, report])
    query_textbox.submit(fn=get_clarifying_questions, inputs=query_textbox, outputs=[questions_out, report])

ui.launch(inbrowser=True)
