# deep_research.py

import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from clarifier_agent import clarifier_agent
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent
from email_agent import email_agent   # ← import the Agent here

# Load environment variables (e.g., SENDGRID_API_KEY)
load_dotenv(override=True)

async def run(query: str, answers: str, state: list[str]):
    """
    Two-phase Gradio workflow:
      1) If `state` is empty, ask clarifying questions.
      2) Once answered, plan → search → write → email → report.
    """
    # Phase 1: Clarify
    if not state:
        clar = await Runner.run(clarifier_agent, query)
        questions = clar.final_output.questions
        qtext = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        return qtext, gr.update(visible=True), questions

    # Phase 2: Full pipeline
    # 1) Bundle user answers for planner
    answered = [
        f"{i+1}. {state[i]} answered: {ans.strip()}"
        for i, ans in enumerate(answers.splitlines())
    ]
    planner_input = f"Original query: {query}\nClarifications:\n" + "\n".join(answered)

    # 2) Generate search plan
    plan_res = await Runner.run(planner_agent, planner_input)
    searches = plan_res.final_output.searches

    # 3) Run each search and collect summaries
    summaries = []
    for item in searches:
        search_res = await Runner.run(search_agent, item.query)
        summaries.append(str(search_res.final_output))

    # 4) Write the full report
    writer_input = f"Original query: {query}\nSummaries: {summaries}"
    write_res = await Runner.run(writer_agent, writer_input)
    report_data = write_res.final_output
    report_md = report_data.markdown_report

    # 5) Email the report
    # Pass the markdown report as the “detailed report” prompt to the email agent
    await Runner.run(email_agent, report_md)

    # Return the markdown report and hide the answers box
    return report_md, gr.update(visible=False), []

# Gradio UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    answers_box = gr.Textbox(
        label="Answer clarifying questions (one per line)",
        visible=False,
        lines=3,
        placeholder="1. …\n2. …\n3. …"
    )
    state = gr.State([])
    report = gr.Markdown(label="Output")
    run_button = gr.Button("Run")

    run_button.click(
        fn=run,
        inputs=[query_textbox, answers_box, state],
        outputs=[report, answers_box, state]
    )

ui.launch(share=False)
