import gradio as gr
import time
from debate_runner import run_debate, run_debate_stream, cancel_debate


def debate_interface(topic):
    if not topic.strip():
        return "Please enter a debate topic."
    
    result = run_debate(topic)
    return result


def test_debate(topic):
    time.sleep(10)
    result = f"""**Summary of Both Positions**
                The debate surrounding {topic}"""
    return result


def handle_button(topic, state, button_label):
    # If currently running → cancel
    if button_label == "Cancel Debate":
        state = cancel_debate(state)
        return (
            "❌ Cancelling debate...",
            state,
            gr.update(value="Start Debate", variant="primary")
        )

    # Otherwise start debate
    generator = run_debate_stream(topic, state)

    # First update button to Cancel
    yield (
        "⏳ Starting debate...\n",
        state,
        gr.update(value="Cancel Debate", variant="stop")
    )

    # Stream debate
    for output, updated_state in generator:
        yield (
            output,
            updated_state,
            gr.update(value="Cancel Debate", variant="stop")
        )

    # When finished → reset button
    yield (
        output,
        updated_state,
        gr.update(value="Start Debate", variant="primary")
    )


with gr.Blocks() as app:
    gr.Markdown("# 🧠 Leadership Calibration Debate Engine")
    gr.Markdown("""Enter any topic and watch two Leadership personas (Technical
    Architect and Engineering Manager) debate and come up with final
    conclusion. \n\n
    The Technical Architect is responsible for the technical aspects of the
    project. \n\n
    The Engineering Manager is responsible for the people aspects of the
    project.""")

    topic_input = gr.TextArea(
        label="Debate Topic",
        placeholder="Example: Should companies adopt a 4-day work week?",
        lines=5
    )

    state = gr.State({"cancelled": False})

    debate_button = gr.Button("Start Debate", variant="primary")

    output = gr.Markdown(visible=True)

    debate_button.click(
        handle_button,
        inputs=[topic_input, state, debate_button],
        outputs=[output, state, debate_button]
    )

if __name__ == "__main__":
    app.queue()
    app.launch()
