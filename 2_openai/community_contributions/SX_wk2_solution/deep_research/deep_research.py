import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from research_manager import research_manager_agent
from clarifier_agent import clarifier_agent

load_dotenv(override=True)


async def get_clarification_questions(topic: str) -> str:
    """Use a dedicated clarifier agent to generate exactly three clarification questions."""
    clarifier_prompt = f"Research topic: {topic}\n\nAsk exactly three clarifying questions."
    result = await Runner.run(clarifier_agent, clarifier_prompt)
    # clarifier_agent returns plain text as final_output
    return str(result.final_output)


async def research_interface(topic: str, user_answers: str):
    trace_id = gen_trace_id()
    print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
    yield f"## 🔎 Starting Research\nView trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
    with trace("Deep Research Trace", trace_id=trace_id):
        # Call the research_workflow tool via the Research Manager agent
        result = await Runner.run(
            research_manager_agent,
            f"Research topic: {topic}\n\nUser clarification answers:\n{user_answers}",
        )
    # research_workflow returns the writer_result.final_output (ReportData)
    yield result.final_output.markdown_report


with gr.Blocks(title="Deep Research Agent", theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# 🔎 Deep Research Agent")

    query_textbox = gr.Textbox(
        label="Research Topic",
        placeholder="What topic would you like to research?",
    )

    questions_md = gr.Markdown(label="Clarification Questions")
    answers_textbox = gr.Textbox(
        label="Your Answers to the Clarification Questions",
        lines=6,
        placeholder="Answer each question clearly here.",
    )

    get_questions_button = gr.Button("First Step: Generate Clarification Questions", variant="secondary")
    run_button = gr.Button("Second Step: Start Research", variant="primary")
    report = gr.Markdown(label="Report")

    # Step 1: generate questions
    get_questions_button.click(
        fn=get_clarification_questions,
        inputs=query_textbox,
        outputs=questions_md,
    )

    # Step 2: run research with topic + answers
    run_button.click(
        fn=research_interface,
        inputs=[query_textbox, answers_textbox],
        outputs=report,
    )

ui.launch(inbrowser=True)

