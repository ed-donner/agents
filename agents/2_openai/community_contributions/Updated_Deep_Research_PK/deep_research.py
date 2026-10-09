import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from clarifier import ClarifyingQuestions, clarifier_agent
from agents import Runner
from contextualizer import ContextualizedQuestions, contextualizing_agent

load_dotenv(override=True)

#func I added
async def submit_answer(answer, answers_list, questions_list, current_index, original_query):
    if not answer or len(answer.strip()) > 100:
        return gr.update(value="Answer must be 1-100 characters."), answers_list, current_index, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), ""

    answers_list.append(answer.strip())
    print("Answer submitted:", answer.strip())

    next_index = current_index + 1
    if next_index < len(questions_list):
        next_question = questions_list[next_index].clarifying_question
        formatted = f"**Q{next_index + 1}**: {next_question}"
        return "", answers_list, next_index, gr.update(value=formatted), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), ""
    else:
        # Once all questions are answered, trigger the contextualizer
        contextualized_query = await run_contextualizer(original_query, questions_list, answers_list)

        # Return the contextualized query and hide other UI elements
        return gr.update(visible=False), answers_list, current_index, gr.update(value=f"**Contextualized Query:** {contextualized_query}"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), contextualized_query

#func I added
async def run_contextualizer(original_query, questions_list, answers_list):
    # Format the prompt string for the contextualizer
    formatted_input = f"Original User Query:\n{original_query.strip()}\n\n"

    print("Questions list:", questions_list)

    for idx, (q, a) in enumerate(zip(questions_list, answers_list), 1):
        formatted_input += (
            f"Clarifying Question {idx}:\n{q.clarifying_question.strip()}\n"
            f"Purpose of clarifying question {idx}:\n{q.question_purpose.strip()}\n"
            f"User Answer for Question {idx}:\n{a.strip()}\n\n"
        )

    # Run the contextualizer agent
    result = await Runner.run(
        contextualizing_agent,
        formatted_input  # This is the prompt the agent will receive
    )

    # Extract and return the contextualized query from the result
    contextualized_query = result.final_output_as(ContextualizedQuestions).contextualized_query
    return contextualized_query


#func I added
async def get_clarifying_questions(query: str) -> ClarifyingQuestions:
    query = query.strip()

    # If the query is invalid (either empty or not within 5-100 characters), return a rejection message and hide the question UI.
    if not query or len(query) < 5 or len(query) > 100:
        return "Please provide a more specific query (5–100 characters).", [], \
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    print("Accumulating clarifying questions...")
    # Run the clarifier agent to generate the clarifying questions based on the user's query.
    result = await Runner.run(
        clarifier_agent,
        f"Query: {query}",
    )

    # Extract the clarifying questions from the agent's output.
    clarifying_questions = result.final_output_as(ClarifyingQuestions).questions

    # Format the first clarifying question to display to the user.
    first_question = clarifying_questions[0]
    formatted = f"**Q1**: {first_question.clarifying_question}\n\n"

    print("Clarifying questions:", clarifying_questions)

    # Return the formatted question, the list of clarifying questions, and make the UI elements for question/answer visible.
    return formatted, clarifying_questions, \
           gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:

    #original code or just a simple change
    """gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=get_clarifying_questions, inputs=query_textbox, outputs=report)
    #run_button.click(fn=run, inputs=query_textbox, outputs=report)
    #query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)"""

    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(label="What topic would you like to research? (5-100 chars)", max_lines=1)
    run_button = gr.Button("Run", variant="primary")

    question_display = gr.Markdown(visible=False)
    answer_box = gr.Textbox(label="Your Answer (5-100 chars)", max_lines=1, visible=False)
    submit_button = gr.Button("Submit Answer", visible=False)

    research_button = gr.Button("Start Research", visible=False)
    research_report = gr.Markdown(label="Research Report", visible=False)

    # States to store clarifying questions and answers
    questions_state = gr.State([])  # List of clarifying questions
    answers_state = gr.State([])    # List of user answers
    question_index = gr.State(0)      # Track current question index
    contextualized_query_state = gr.State("")  # Store the contextualized query

    run_button.click(
    fn=get_clarifying_questions,
    inputs=query_textbox,
    outputs=[
        question_display,       # text update
        questions_state,        # state update
        question_display,       # visibility update
        answer_box,             # visibility update
        submit_button           # visibility update
    ]
    )

    submit_button.click(
    fn=submit_answer,
    inputs=[answer_box, answers_state, questions_state, question_index, query_textbox],
    outputs=[answer_box, answers_state, question_index, question_display, submit_button, research_button, research_report, contextualized_query_state]
    )

    research_button.click(
        fn=run,
        inputs=contextualized_query_state,
        outputs=research_report
    )

ui.launch(inbrowser=True)

