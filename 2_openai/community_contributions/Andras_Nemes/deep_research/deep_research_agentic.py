import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from agents.exceptions import MaxTurnsExceeded
from research_manager import ResearchManager
from research_agent import research_manager_agent, build_manager_input, ConsoleLogHooks
from email_agent import email_agent

load_dotenv(override=True)

# ResearchManager is reused only for the clarify() step and the format_clarifications() helper.
# The research phase itself is driven by the autonomous research_manager_agent.
manager = ResearchManager()


async def get_clarifications(query: str):
    """ Stage 1 (unchanged): ask the clarifier agent for questions and reveal the answer panel. """
    questions = await manager.clarify(query)
    questions = (questions + ["", "", ""])[:3]
    return (
        questions,
        gr.update(visible=True),
        gr.update(label=questions[0], value=""),
        gr.update(label=questions[1], value=""),
        gr.update(label=questions[2], value=""),
    )


async def run_research(query: str, questions: list[str], a1: str, a2: str, a3: str):
    """ Stage 2: hand the query and clarifications to the autonomous manager agent, which decides
    how to orchestrate the planner/search/evaluator/writer/email tools. """
    clarifications = ResearchManager.format_clarifications(questions, [a1, a2, a3])
    trace_id = gen_trace_id()
    with trace("Research trace (agentic)", trace_id=trace_id):
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
        yield "The Research Manager agent is orchestrating its tools (plan, search, evaluate, write, email)..."
        print("\n=== Agentic research run started ===", flush=True)
        print(f"Query: {query}", flush=True)
        print(f"Clarifications: {clarifications or '(none)'}", flush=True)
        print("Watch this console for the manager's tool calls...\n", flush=True)
        try:
            hooks = ConsoleLogHooks()
            result = await Runner.run(
                research_manager_agent,
                build_manager_input(query, clarifications),
                hooks=hooks,
                max_turns=40,  # the manager may make many tool calls (plan + several searches + evaluate loops)
            )
            print("=== Agentic research run complete ===\n", flush=True)
            report = result.final_output
            # Code-level guarantee: LLM orchestration may skip the email step, so send it ourselves.
            if "send_report_email" not in hooks.called_tools:
                yield "The manager skipped the email step, sending the report by email now..."
                print("[fallback] manager did not call send_report_email, sending directly", flush=True)
                try:
                    await Runner.run(email_agent, report)
                    print("[fallback] email sent", flush=True)
                except Exception as e:
                    print(f"[fallback] email failed: {e}", flush=True)
            yield report
        except MaxTurnsExceeded:
            print("=== Run stopped: max turns exceeded ===\n", flush=True)
            yield ("The manager agent took too many steps and was stopped. This can happen with "
                   "autonomous orchestration. Try running again, or simplify the query.")


with gr.Blocks() as ui:
    gr.Markdown("# Deep Research (agentic manager)")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Get clarifying questions", variant="primary")

    questions_state = gr.State([])
    with gr.Column(visible=False) as clarify_panel:
        gr.Markdown("**Please answer these clarifying questions, then run the research:**")
        answer1 = gr.Textbox(label="Answer 1")
        answer2 = gr.Textbox(label="Answer 2")
        answer3 = gr.Textbox(label="Answer 3")
        research_button = gr.Button("Run research", variant="primary")
    report = gr.Markdown(label="Report")

    clarify_button.click(
        fn=get_clarifications,
        inputs=query_textbox,
        outputs=[questions_state, clarify_panel, answer1, answer2, answer3],
    )
    research_button.click(
        fn=run_research,
        inputs=[query_textbox, questions_state, answer1, answer2, answer3],
        outputs=report,
    )

ui.launch(theme=gr.themes.Default(primary_hue="sky"), inbrowser=True)
