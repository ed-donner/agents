import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()

# Global variable to hold dynamically created textboxes
clarification_textboxes = []


def bind_run_button_click(run_button, clarification_textboxes, original_query_state, status_message, report_output):
    run_button.click(
        run_full_research,
        inputs=clarification_textboxes + [original_query_state],
        outputs=[
            status_message,
            report_output,     # NEW
        ],
        show_progress="full"
    )


async def clarify_and_store(query):
    questions = await manager.get_clarifying_questions(query)
    print("DEBUG: questions returned =", questions) 
    status = "✅ Clarification questions generated." if questions else "Query is already clear. Ready to research."
    return (
        # gr.update(questions, visible=True), # show clarification_box
        questions,
        query, # store original query
        status,
        gr.update(visible=True) # Show the Run button only now
    )

async def run_full_research(*answers_and_query):
    *answers, original_query = answers_and_query
    status = "🔍 Running full research..."
    yield status, gr.update(visible=True)  # Optional spinner refresh
    
    refined_query = manager.refine_query_with_answers(original_query, answers)
    chunks = []
    async for chunk in manager.run(refined_query):
        chunks.append(chunk)
        yield f"📄 {len(chunks)} section(s) completed...", gr.update(visible=True)
    
    final_output = "\n\n".join(chunks)
    yield "✅ Research complete.", final_output

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research Tool with Clarification")

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Submit for clarifying questions", variant="secondary")

    clarification_container = gr.Column(visible=False)
    clarification_textboxes = []
    with clarification_container:
        for _ in range(3):  # or any number of max clarifying questions
            tb = gr.Textbox(visible=False, lines=2)
            clarification_textboxes.append(tb)
    
    clarification_question_state = gr.State()
    
    original_query_state = gr.State()

    # ✅ NEW: Status message
    status_message = gr.Markdown("")
    report_output = gr.Markdown(label="Research Report")

    run_button = gr.Button("Run Full Research", variant="primary", visible=False)
    
    # 
    def render_clarification_ui(questions):
        
        print("DEBUG: rendering UI with questions =", questions)

        textbox_updates = []
        
        # Add guard clause to avoid calling len() on None:
        if not questions:
            # If no questions, hide all textboxes
            textbox_updates = [gr.update(visible=False) for _ in clarification_textboxes]
        else:

            for i, tb in enumerate(clarification_textboxes):
                if i < len(questions):
                    textbox_updates.append(gr.update(visible=True, label=questions[i]))
                else:
                    textbox_updates.append(gr.update(visible=False))

        # clarification_container.visible = True
        # run_button.visible = True

        # Return the container and run button to update their visibility/children in UI
        return *textbox_updates, gr.update(visible=True), gr.update(visible=True)

    clarify_button.click(
        clarify_and_store,
        inputs=query_textbox,
        outputs=[
            clarification_question_state,  # list[str]
            original_query_state,          # str
            # clarification_box, 
            status_message,     # NEW
            clarification_container        # make group visible
        ],
        show_progress="full"
    ).then(
            render_clarification_ui,
            inputs=clarification_question_state,
            outputs=clarification_textboxes + [clarification_container, run_button]
    ).then(
        lambda: gr.update(interactive=False),
        inputs=None,
        outputs=clarify_button
    )

    bind_run_button_click(
        run_button, 
        clarification_textboxes, 
        original_query_state, 
        status_message, 
        report_output
    )

ui.launch(inbrowser=True, share=True)
