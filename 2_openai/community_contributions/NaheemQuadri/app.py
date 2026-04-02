from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import gradio as gr
from research_manager import ResearchManager

manager = ResearchManager()

WELCOME_MESSAGE = """Welcome to the Deep Research Agent

I can help you produce a comprehensive, well-structured research report on any topic. Here's how it works:

1. Enter your query — type any research topic or question below
2. Answer 3 quick questions — I'll ask about report type, focus, audience, and timeframe so the research is tailored to your needs
3. Relax — I'll search the web, synthesise the findings, write a detailed report, and email it to you

Ready? Enter your research topic below to get started!"""

CLARIFYING_QUESTIONS = [
    "What type of report/research do you want? And What is the specific angle or perspective you want the report to focus on?",
    "Who is the target audience — technical experts, general public, executives?",
    "What time range or recency matters most — latest developments, historical overview, or both?",
]


async def start_research(query: str, history: list, answers: dict):
    
    if not query.strip() or len(query.strip()) < 10:
        history.append({"role": "user", "content": query})
        history.append({
            "role": "assistant",
            "content": "Please enter a meaningful research topic to get started.",
        })
        return history, answers, gr.update(visible=True), gr.update(visible=False)

    history.append({"role": "user", "content": query})
    answers["query"] = query
    answers["responses"] = []
    answers["q_index"] = 0

    history.append({
        "role": "assistant",
        "content": (
            f"Great topic! Before I start researching, I have a few quick questions "
            f"to make sure the report is tailored to your needs.\n\n"
            f"Question 1 of {len(CLARIFYING_QUESTIONS)}: {CLARIFYING_QUESTIONS[0]}"
        ),
    })
    return history, answers, gr.update(visible=False), gr.update(visible=True)


async def handle_answer(answer: str, history: list, answers: dict):
    
    history.append({"role": "user", "content": answer})
    answers["responses"].append(answer)
    answers["q_index"] += 1

    
    if answers["q_index"] < len(CLARIFYING_QUESTIONS):
        next_q = CLARIFYING_QUESTIONS[answers["q_index"]]
        history.append({
            "role": "assistant",
            "content": (
                f"Question {answers['q_index'] + 1} of {len(CLARIFYING_QUESTIONS)}: {next_q}"
            ),
        })
        yield history, answers
        return

    
    history.append({
        "role": "assistant",
        "content": (
            "Thanks! I have everything I need. Starting the research pipeline now...\n\n"
        ),
    })
    yield history, answers

    enriched_query = (
        f"Query: {answers['query']}\n\n"
        f"Clarifications:\n"
        + "\n".join(
            f"Q: {CLARIFYING_QUESTIONS[i]}\nA: {answers['responses'][i]}"
            for i in range(len(CLARIFYING_QUESTIONS))
        )
        + "\n\nIMPORTANT: Structure and tone the final report according to the report type specified above."
    )

    async for update in manager.run(enriched_query):
        history.append({"role": "assistant", "content": update})
        yield history, answers


with gr.Blocks() as demo:
    gr.Markdown("# Deep Research Agent")

    answers_state = gr.State({})
    chatbot = gr.Chatbot(
        value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
        type="messages",
        label="Research Pipeline",
        height=600,
        render_markdown=True,
    )

    with gr.Row(visible=True) as query_row:
        query_box = gr.Textbox(
            placeholder="Enter your research topic...",
            label="Research Query",
            scale=9,
        )
        start_btn = gr.Button("Start", scale=1, variant="primary")

    with gr.Row(visible=False) as answer_row:
        answer_box = gr.Textbox(
            placeholder="Type your answer...",
            label="Answer",
            scale=9,
        )
        answer_btn = gr.Button("Submit", scale=1, variant="primary")

    start_btn.click(
        fn=start_research,
        inputs=[query_box, chatbot, answers_state],
        outputs=[chatbot, answers_state, query_row, answer_row],
    )
    query_box.submit(
        fn=start_research,
        inputs=[query_box, chatbot, answers_state],
        outputs=[chatbot, answers_state, query_row, answer_row],
    )
    answer_btn.click(
        fn=handle_answer,
        inputs=[answer_box, chatbot, answers_state],
        outputs=[chatbot, answers_state],
    )
    answer_box.submit(
        fn=handle_answer,
        inputs=[answer_box, chatbot, answers_state],
        outputs=[chatbot, answers_state],
    )

if __name__ == "__main__":
    demo.launch()