from agents import Runner, gen_trace_id, trace
import gradio as gr
from dotenv import load_dotenv
from research_manager import get_clarification_questions, refine_query, research_manager

load_dotenv(override=True)


async def start_chat(query: str):
    clarification = await get_clarification_questions(query)
    questions = clarification.questions[:3]
    while len(questions) < 3:
        questions.append("")

    return (
        [(query, questions[0])],
        "",
        query,
        questions,
        [],
        0,
    )


async def continue_chat(
    message: str,
    history: list[tuple[str, str]],
    original_query: str,
    questions: list[str],
    answers: list[str],
    question_index: int,
):
    updated_history = history + [(message, "")]
    updated_answers = answers + [message]
    next_index = question_index + 1

    if next_index < len(questions):
        updated_history[-1] = (message, questions[next_index])
        yield updated_history, "", original_query, questions, updated_answers, next_index
        return

    refined_query = await refine_query(original_query, questions, updated_answers)
    updated_history[-1] = (
        message,
        f"Refined query:\n\n{refined_query}\n\nStarting research...",
    )

    yield updated_history, "", refined_query, questions, updated_answers, next_index

    trace_id = gen_trace_id()
    with trace("Research trace", trace_id=trace_id):
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        result = await Runner.run(research_manager, refined_query)
        report = result.final_output
    updated_history[-1] = (
        message,
        f"Refined query:\n\n{refined_query}\n\nView trace: {trace_url}\n\n{report.markdown_report}",
    )
    yield updated_history, "", refined_query, questions, updated_answers, next_index


async def handle_message(
    message: str,
    history: list[tuple[str, str]],
    original_query: str,
    questions: list[str],
    answers: list[str],
    question_index: int,
):
    if not message.strip():
        yield history, "", original_query, questions, answers, question_index
        return

    if not original_query:
        yield await start_chat(message)
        return

    async for update in continue_chat(
        message,
        history,
        original_query,
        questions,
        answers,
        question_index,
    ):
        yield update


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    original_query_state = gr.State("")
    clarification_questions = gr.State([])
    clarification_answers = gr.State([])
    question_index = gr.State(0)

    gr.Markdown("# Deep Research")
    chatbot = gr.Chatbot(label="Deep Research", type="tuples", height=500)
    query_textbox = gr.Textbox(
        label="Start a research request or answer the current clarification question"
    )
    send_button = gr.Button("Send", variant="primary")

    send_button.click(
        fn=handle_message,
        inputs=[
            query_textbox,
            chatbot,
            original_query_state,
            clarification_questions,
            clarification_answers,
            question_index,
        ],
        outputs=[
            chatbot,
            query_textbox,
            original_query_state,
            clarification_questions,
            clarification_answers,
            question_index,
        ],
    )

    query_textbox.submit(
        fn=handle_message,
        inputs=[
            query_textbox,
            chatbot,
            original_query_state,
            clarification_questions,
            clarification_answers,
            question_index,
        ],
        outputs=[
            chatbot,
            query_textbox,
            original_query_state,
            clarification_questions,
            clarification_answers,
            question_index,
        ],
    )

ui.launch(inbrowser=True)
