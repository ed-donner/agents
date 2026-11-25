import gradio as gr
from dotenv import load_dotenv
from styles import CSS, JS, EXAMPLES, HEADER_HTML
from agents_as_tools import run as run_agengts_as_tools

load_dotenv(override=True)

async def run(query, clarifying_q, clarifying_a, trace_id):
    async for (clarifiers_state, clarifiers_display, user_box, submit_answers_btn, report_display, trace_id_state) in run_agengts_as_tools(query, clarifying_q, clarifying_a, trace_id):
        yield (clarifiers_state, clarifiers_display, user_box, submit_answers_btn, report_display, trace_id_state)

with gr.Blocks(title="Deep Research") as ui:
    gr.HTML(HEADER_HTML)

    with gr.Row(elem_classes="dr-query-row"):
        query_textbox = gr.Textbox(
            placeholder="Type a research question...",
            show_label=False,
            container=False,
            autofocus=True,
            elem_id="dr-query",
            scale=5,
        )
        run_button = gr.Button("Investigate", variant="primary", elem_id="dr-run", scale=1)

    gr.HTML('<div class="dr-examples-label">Try one</div>')
    gr.Examples(examples=EXAMPLES, inputs=query_textbox, elem_id="dr-examples")

    clarifiers_state = gr.State([])
    clarifiers_display = gr.Markdown(elem_id="dr-clarfyiers")

    user_box = gr.Textbox(
        label="Please Clarify",
        placeholder="Your Answere Here",
        lines=4,
        visible=False,
      )

    submit_answers_btn = gr.Button("Continue", visible=False)
    report_display = gr.Markdown(label="Final Report")
    trace_id_state = gr.State("")


    pipeline_inputs = [query_textbox, clarifiers_state, user_box, trace_id_state]
    pipeline_outputs = [
        clarifiers_state,
        clarifiers_display,
        user_box,
        submit_answers_btn,
        report_display,
        trace_id_state
    ]
    run_button.click(
      fn=run,
      inputs=pipeline_inputs,
      outputs=pipeline_outputs,
    ) 
    query_textbox.submit(
        fn=run,
        inputs=pipeline_inputs,
        outputs=pipeline_outputs,
    )

    submit_answers_btn.click(
        fn=run,
        inputs=pipeline_inputs,
        outputs=pipeline_outputs,
    )

if __name__ == "__main__":
    ui.launch(css=CSS, js=JS, theme=gr.themes.Base())
