import asyncio
import tracing
import gradio as gr
from dotenv import load_dotenv
from research_manager import ClarificationRequest, ResearchManager

load_dotenv(override=True)

pending_answers: dict[str, asyncio.Future] = {}


async def run(query: str, request: gr.Request):

    if not query.strip():
        raise gr.Error("Please enter a research topic.")

    session_id = request.session_hash

    if not session_id:
        raise gr.Error("Session is unavailable.")

    if session_id in pending_answers:
        raise gr.Error("Research is already awaiting answers.")

    generator = ResearchManager().run(query)

    next_input = None

    try:
        while True:
            try:
                event = await generator.asend(next_input)
                next_input = None

            except StopAsyncIteration:
                break

            if isinstance(event, ClarificationRequest):
                if len(event.questions) != 3:
                    raise gr.Error("Expected exactly 3 questions.")

                future = asyncio.get_running_loop().create_future()
                pending_answers[session_id] = future

                yield (
                    gr.update(),
                    gr.update(visible=True),
                    gr.update(label=event.questions[0], value=""),
                    gr.update(label=event.questions[1], value=""),
                    gr.update(label=event.questions[2], value=""),
                    gr.update(interactive=True),
                )

                try:
                    answers = await asyncio.wait_for(
                        future,
                        timeout=1800,
                    )
                except asyncio.TimeoutError:
                    yield (
                        "Research stopped: clarification timed out.",
                        gr.update(visible=False),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        gr.update(interactive=False),
                    )
                    return
                finally:
                    if pending_answers.get(session_id) is future:
                        del pending_answers[session_id]

                next_input = answers

                yield (
                    gr.update(),
                    gr.update(visible=False),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(interactive=False),
                )

            else:
                yield (
                    event,
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )

    finally:
        future = pending_answers.pop(session_id, None)

        if future is not None and not future.done():
            future.cancel()

        await generator.aclose()


async def submit_answers(
    answer1: str,
    answer2: str,
    answer3: str,
    request: gr.Request,
):
    answers = [answer1, answer2, answer3]

    if not all(answer.strip() for answer in answers):
        raise gr.Error("Please answer all 3 questions.")

    future = pending_answers.get(request.session_hash)

    if future is None or future.done():
        raise gr.Error("No clarification request is pending.")

    future.set_result(answers)

    return gr.update(interactive=False)


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:

    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(label="What topic would you like to research?")

    run_button = gr.Button("Run", variant="primary")

    report = gr.Markdown(label="Report")

    with gr.Column(visible=False) as questions_panel:
        gr.Markdown("### Clarifying questions")

        answer1 = gr.Textbox(label="Question 1")
        answer2 = gr.Textbox(label="Question 2")
        answer3 = gr.Textbox(label="Question 3")

        continue_button = gr.Button("Continue Research", variant="primary")

    gr.on(
        triggers=[run_button.click, query_textbox.submit],
        fn=run,
        inputs=[query_textbox],
        outputs=[
            report,
            questions_panel,
            answer1,
            answer2,
            answer3,
            continue_button,
        ],
        trigger_mode="once",
        concurrency_limit=None,
    )

    continue_button.click(
        fn=submit_answers,
        inputs=[answer1, answer2, answer3],
        outputs=[continue_button],
        queue=False,
    )

ui.queue().launch()
