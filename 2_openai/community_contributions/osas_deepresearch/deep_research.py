import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

MAX_QUESTIONS = 5


async def get_questions(query: str):
    """Ask the agentic clarifier how many questions to ask (0–5), then reveal the answer widgets."""
    if not query or not query.strip():
        return [gr.update()] * (MAX_QUESTIONS * 2 + 3)  # state + status + radios + other_boxes + run_btn

    manager = ResearchManager()
    questions = await manager.generate_clarifying_questions(query)  # list[dict]

    updates = []

    # 1. State
    updates.append(questions)

    # 2. Status message
    if not questions:
        updates.append(gr.update(value="✓ Query is specific — no clarification needed.", visible=True))
    else:
        updates.append(gr.update(value=f"Please answer {len(questions)} question(s) below:", visible=True))

    # 3. Radio buttons — show only as many as the agent decided
    for i in range(MAX_QUESTIONS):
        if i < len(questions):
            q = questions[i]
            updates.append(gr.update(
                label=q["question"],
                choices=q["options"] + ["Other"],
                value=None,
                visible=True,
            ))
        else:
            updates.append(gr.update(visible=False, value=None))

    # 4. "Other" textboxes — all hidden; change handlers will reveal them as needed
    for _ in range(MAX_QUESTIONS):
        updates.append(gr.update(visible=False, value=""))

    # 5. Run button
    updates.append(gr.update(visible=True))

    return updates


def make_other_toggle(radio, other_box):
    """Wire a radio button so its paired 'Other' textbox appears only when 'Other' is selected."""
    radio.change(
        fn=lambda v: gr.update(visible=(v == "Other"), value=""),
        inputs=[radio],
        outputs=[other_box],
    )


async def run_research(query: str, *args):
    """Run the full research pipeline using query + clarification answers."""
    # args layout: radio_0..4, other_0..4, questions_state
    radio_vals = list(args[:MAX_QUESTIONS])
    other_vals = list(args[MAX_QUESTIONS: MAX_QUESTIONS * 2])
    questions_state: list[dict] = args[MAX_QUESTIONS * 2]

    clarifications = None
    if questions_state:
        pairs = []
        for i, q_dict in enumerate(questions_state):
            if i >= MAX_QUESTIONS:
                break
            radio_val = radio_vals[i]
            other_val = other_vals[i] or ""
            answer = other_val.strip() if radio_val == "Other" else (radio_val or "")
            if answer:
                pairs.append((q_dict["question"], answer))
        if pairs:
            clarifications = pairs

    async for chunk in ResearchManager().run(query, clarifications):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    questions_state = gr.State([])

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    ask_button = gr.Button("Get Clarifying Questions", variant="secondary")

    status_msg = gr.Markdown(visible=False)

    # Pre-create MAX_QUESTIONS radio + other-text pairs
    radios = []
    other_boxes = []
    for _ in range(MAX_QUESTIONS):
        radio = gr.Radio(label="", choices=[], visible=False, interactive=True)
        other_box = gr.Textbox(label="Please specify:", visible=False, interactive=True, lines=1)
        radios.append(radio)
        other_boxes.append(other_box)
        make_other_toggle(radio, other_box)

    run_button = gr.Button("Run Research", variant="primary", visible=False)
    report = gr.Markdown(label="Report")

    ask_button.click(
        fn=get_questions,
        inputs=[query_textbox],
        outputs=[questions_state, status_msg] + radios + other_boxes + [run_button],
    )

    run_button.click(
        fn=run_research,
        inputs=[query_textbox] + radios + other_boxes + [questions_state],
        outputs=report,
    )

ui.launch(inbrowser=True)
