import gradio as gr

from showdown import build_football_debate_team, stream_live_transcript

DEFAULT_TOPIC = (
    "Debate who has had a more impressive season so far in 2026: "
    "Chelsea or Manchester City?"
)

EXAMPLE_DEBATES: dict[str, str] = {
    "2026 season — Chelsea vs City": DEFAULT_TOPIC,
    "Tactics — possession vs transition": (
        "Debate which tactical identity is more effective in the Premier League today: "
        "Manchester City's control-and-overload approach, or Chelsea's direct, "
        "transition-heavy style when both squads are healthy."
    ),
    "Youth academy — Cobham vs City academy": (
        "Argue which club's academy pathway and first-team integration has been more "
        "impressive recently: Chelsea's Cobham graduates or Manchester City's youth pipeline."
    ),
    "European nights — UCL pedigree": (
        "Debate which club has the stronger claim to being a Champions League heavyweight "
        "over the last decade: Chelsea or Manchester City, using finals, knockouts, and "
        "memorable ties."
    ),
    "Club identity — history vs modern dominance": (
        "Settle this tension: is Chelsea's legacy and 'London is Blue' culture a bigger "
        "asset than Manchester City's era of sustained domestic dominance and trophies "
        "under Guardiola?"
    ),
}

EMPTY_STATE = "No Live Transcript yet. Enter a topic below and click Run debate"

APP_TITLE = """# Warm Up+ - The dedicated football talk show.

*Moderated multi-agent debate · Chelsea vs Manchester City*

Choose an example or write your own topic, then press **Run debate** to hear both sides and the moderator's verdict.
"""


def header_markdown(topic: str) -> str:
    return (
        "## Warm Up+ - The dedicated football talk show\n\n"
        f"*Live session ·* **Topic:** {topic}\n"
    )


async def run_debate(topic: str):
    topic = (topic or "").strip()
    if not topic:
        yield "*Please enter a debate topic.*"
        return

    team = build_football_debate_team()
    header = header_markdown(topic)
    yield header + "\n\n*Agents are debating…*\n"

    async for chunk in stream_live_transcript(team, task=topic):
        yield header + chunk


def restart_debate() -> str:
    """Clear the transcript so the user can start fresh (same or new topic)."""
    return EMPTY_STATE


def apply_example_choice(choice: str | None) -> str:
    """Load the selected example into the topic field."""
    if not choice:
        return DEFAULT_TOPIC
    return EXAMPLE_DEBATES.get(choice, DEFAULT_TOPIC)


def launch():
    with gr.Blocks(
        title="Warm Up+",
    ) as demo:
        gr.Markdown(APP_TITLE)
        example_radio = gr.Radio(
            label="Example debates",
            choices=list(EXAMPLE_DEBATES.keys()),
            value="2026 season — Chelsea vs City",
            container=True,
        )
        topic = gr.Textbox(
            label="Debate topic",
            value=DEFAULT_TOPIC,
            lines=4,
        )
        example_radio.change(
            fn=apply_example_choice,
            inputs=[example_radio],
            outputs=[topic],
        )
        with gr.Row():
            run_btn = gr.Button("Run debate", variant="primary")
            reset_btn = gr.Button("Restart debate", variant="secondary")

        transcript = gr.Markdown(
            value=EMPTY_STATE,
            label="Transcript",
            show_label=True,
            show_copy_button=True,
            container=True,
            min_height=360,
            line_breaks=True,
            latex_delimiters=[],
        )

        run_btn.click(fn=run_debate, inputs=[topic], outputs=[transcript])
        reset_btn.click(fn=restart_debate, inputs=[], outputs=[transcript])

    demo.queue(default_concurrency_limit=1)
    demo.launch()


if __name__ == "__main__":
    launch()
