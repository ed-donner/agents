import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)
manager = ResearchManager()

with gr.Blocks() as ui:
    gr.Markdown("# 🔎 Deep Research (Orchestrator-driven)")

    # State for query + clarifications
    state = gr.State({"query": None, "clarifications": None})

    # Step 1: User enters query
    query_box = gr.Textbox(label="What topic do you want to research?")
    submit_question_btn = gr.Button("Submit Question", variant="primary")

    # Step 2: Clarifier questions + answer field
    clarifying_qs_box = gr.Markdown(visible=False)
    clarifications_box = gr.Textbox(
        label="Your clarifications (if any):", visible=False,
        placeholder="Answer clarifier questions here before running full research..."
    )
    submit_clarifications_btn = gr.Button("Run Research", visible=False)

    # Step 3: Output + reset button
    report_md = gr.Markdown(visible=False)
    back_btn = gr.Button("🔄 Back to Start", visible=False)

    # Step 1 handler: ask clarifier
    async def get_questions(query, state):
        questions = await manager.clarify_query(query)
        state["query"] = query
        if questions:
            return (
                state,
                gr.update(value="\n".join([f"- {q}" for q in questions]), visible=True),  # clarifying_qs_box
                gr.update(visible=True),                                                 # clarifications_box
                gr.update(visible=True),                                                 # submit_clarifications_btn
                gr.update(value="", visible=False),                                      # report_md (hide output)
                gr.update(visible=False)                                                 # back_btn
            )
        else:
            # If no clarifier questions → run orchestrator directly
            result = await manager.run(query, "")
            return (
                state,
                gr.update(value="", visible=False),     # clarifying_qs_box
                gr.update(value="", visible=False),     # clarifications_box
                gr.update(visible=False),               # submit_clarifications_btn
                gr.update(value=result, visible=True),  # report_md
                gr.update(visible=True)                 # back_btn
            )

    # Step 2 handler: run orchestrated research
    async def run_research(query, clarifications, state):
        state["clarifications"] = clarifications
        result = await manager.run(query, clarifications)
        return (
            state,
            gr.update(value="", visible=False),        # clarifying_qs_box
            gr.update(value="", visible=False),        # clarifications_box
            gr.update(visible=False),                  # submit_clarifications_btn
            gr.update(value=result, visible=True),     # report_md
            gr.update(visible=True)                    # back_btn
        )

    # Step 3 handler: reset
    def reset_app():
        return (
            gr.update(value="", visible=True),      # query_box
            gr.update(value="", visible=False),     # clarifying_qs_box
            gr.update(value="", visible=False),     # clarifications_box
            gr.update(visible=False),               # submit_clarifications_btn
            gr.update(value="", visible=False),     # report_md
            gr.update(visible=False),               # back_btn
            {"query": None, "clarifications": None} # reset state
        )

    # Wire up events
    submit_question_btn.click(
        get_questions,
        [query_box, state],
        [state, clarifying_qs_box, clarifications_box, submit_clarifications_btn, report_md, back_btn]
    )
    submit_clarifications_btn.click(
        run_research,
        [query_box, clarifications_box, state],
        [state, clarifying_qs_box, clarifications_box, submit_clarifications_btn, report_md, back_btn]
    )
    back_btn.click(
        reset_app,
        None,
        [query_box, clarifying_qs_box, clarifications_box, submit_clarifications_btn, report_md, back_btn, state]
    )

ui.launch(inbrowser=True)
