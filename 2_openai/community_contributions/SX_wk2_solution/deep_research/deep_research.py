import asyncio
import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from planner_agent import planner_agent
from search_agent import search_agent
from analyser_agent import analyser_agent
from writer_agent import writer_agent
from reviewer_agent import reviewer_agent
from email_agent import email_agent
from clarifier_agent import clarifier_agent

load_dotenv(override=True)


async def get_clarification_questions(topic: str) -> str:
    """Use a dedicated clarifier agent to generate exactly three clarification questions."""
    clarifier_prompt = f"Research topic: {topic}\n\nAsk exactly three clarifying questions."
    result = await Runner.run(clarifier_agent, clarifier_prompt)
    # clarifier_agent returns plain text as final_output
    return str(result.final_output)


async def research_interface(topic: str, user_answers: str):
    log = []

    def emit(msg: str) -> str:
        log.append(msg)
        return "\n\n".join(log)

    trace_id = gen_trace_id()
    trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
    print(f"View trace: {trace_url}")
    yield emit (f"### 🔎 Starting Research\nView trace: {trace_url}")

    # Initial context includes topic + user clarification answers
    research_context = (
        f"Research Topic:\n{topic}\n\n"
        f"User Clarification Answers:\n{user_answers}\n\n"
    )

    combined_results = []
    iteration = 0
    max_iterations = 2

    with trace("Deep Research Trace", trace_id=trace_id):
        while iteration < max_iterations:
            # 1. Plan searches
            yield emit (f"### 🧭 Planning web search... (iteration {iteration + 1})")
            planner_result = await Runner.run(planner_agent, research_context)
            searches = planner_result.final_output

            # 2. Execute searches concurrently
            yield emit (f"### 🌐 Starting web search... (iteration {iteration + 1})")
            tasks = [Runner.run(search_agent, q.query) for q in searches.searches]
            search_results = await asyncio.gather(*tasks)

            # 3. Collect summaries
            yield emit (f"### 📚 Collating web search results... (iteration {iteration + 1})")
            combined_results.extend([r.final_output for r in search_results])

            # 4. Analyse completeness
            yield emit (f"### 🧪 Analysing quality of search results... (iteration {iteration + 1})")
            analysis = await Runner.run(analyser_agent, str(combined_results))
            if analysis.final_output.research_complete:
                yield emit ("### ✅ Research judged complete by analyser agent.")
                break

            # If incomplete, append reason to context and iterate again
            research_context += f"\nAdditional research needed: {analysis.final_output.reason}\n"
            yield emit (f"### 🔁 Additional research needed: {analysis.final_output.reason}")
            iteration += 1

        # Prepare clean text for writer
        summaries_text = "\n\n---\n\n".join(combined_results)

        writer_input = (
            "You are writing a full research report.\n\n"
            f"Original Topic:\n{topic}\n\n"
            f"User Clarification Answers:\n{user_answers}\n\n"
            f"Initial Research Summaries:\n{summaries_text}\n"
        )

        yield emit ("### ✍️ Searches complete, writing report...")
        writer_output = await Runner.run(writer_agent, writer_input)

        yield emit ("### 📝 Report drafted, reviewing report...")
        reviewer_output = await Runner.run(reviewer_agent, writer_output.final_output.markdown_report)

        yield emit("### 📧 Review complete, sending email...")
        await Runner.run(email_agent, reviewer_output.final_output.markdown_report)

        yield emit("### 🔎 Email sent, research complete.")
        # Finally, show the full report in the UI
        yield reviewer_output.final_output.markdown_report


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

    get_questions_button = gr.Button("First Step --- Generate Clarification Questions", variant="primary")
    run_button = gr.Button("Second Step --- Start Research", variant="primary")
    report = gr.Markdown(label="Report")

    # Step 1: generate questions
    get_questions_button.click(
        fn=get_clarification_questions,
        inputs=query_textbox,
        outputs=questions_md,
    )

    # Step 2: run research with topic + answers (streaming)
    run_button.click(
        fn=research_interface,
        inputs=[query_textbox, answers_textbox],
        outputs=report,
    )

ui.launch(inbrowser=True)

