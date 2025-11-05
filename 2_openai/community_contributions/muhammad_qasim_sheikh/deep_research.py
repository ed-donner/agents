import gradio as gr
from dotenv import load_dotenv
from agents import Runner, gen_trace_id
from clarifier_agent import clarification_agent, ClarifyingQuestions
from master_agent import master_agent
import asyncio

load_dotenv(override=True)

async def chat_flow(message: str, state: dict):
    """
    This function manages the conversation state and yields new assistant messages.
    """
    current_step = state.get("step", "START")
    
    if current_step == "START":
        #Start Clarification
        state["original_query"] = message
        state["qa_pairs"] = [] 
        state["question_index"] = 0

        yield "That's a great topic. To give you the best possible report, I have a few clarifying questions. This will only take a moment."

        try:
            result = await Runner.run(clarification_agent, f"Query: {message}")
            questions = result.final_output_as(ClarifyingQuestions).questions
            state["questions_list"] = questions

            first_question = questions[0]
            state["step"] = "CLARIFYING"
            yield first_question

        except Exception as e:
            yield f"Sorry, an error occurred during clarification: {e}"
            state["step"] = "START"  

    elif current_step == "CLARIFYING":
        answer = message
        question_index = state["question_index"]
        question_asked = state["questions_list"][question_index]

        state["qa_pairs"].append((question_asked, answer))

        state["question_index"] += 1

        if state["question_index"] < len(state["questions_list"]):
            next_question = state["questions_list"][state["question_index"]]
            yield next_question

        else:
            state["step"] = "RESEARCH_IN_PROGRESS"

            full_query_context = f"Original Query: {state['original_query']}\n\n--- Clarification Transcript ---\n"
            for q, a in state["qa_pairs"]:
                full_query_context += f"Question: {q}\nAnswer: {a}\n\n"

            trace_id = gen_trace_id()
            trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print(f"View trace: {trace_url}")

            yield f"Thank you, that's perfect. Starting the deep research with this enhanced context. This may take several minutes.\n\n[View Live Trace]({trace_url})"

            try:
                result = await Runner.run(master_agent, full_query_context)

                try:
                    final_report = result.final_output.content[0].text.value
                except Exception:
                    final_report = str(result.final_output)

                yield final_report
                state["step"] = "START"

            except Exception as e:
                yield f"Sorry, an error occurred during research: {e}"
                state["step"] = "START"

    elif current_step == "RESEARCH_IN_PROGRESS":
        yield "Research is already in progress. Please wait until it is complete."

async def gradio_chat_wrapper(message: str, history_with_state: list):
    """
    This wrapper now correctly manages the history list for the chatbot.
    """
    if not history_with_state:
        history = []
        state = {"step": "START"}
    else:
        history = history_with_state[0] 
        state = history_with_state[1]   

    history.append({"role": "user", "content": message})
    yield history

    async for new_content in chat_flow(message, state):
        if new_content:
            assistant_message = {"role": "assistant", "content": new_content}
            history.append(assistant_message)
            history_with_state[:] = [history, state]

            yield history


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research Agent (Agentic Workflow)")
    gr.Markdown("Submit a research topic. The agent will ask clarifying questions one-by-one, then run an autonomous research loop to generate and email a report.")

    chat_state = gr.State(value=[]) 

    chatbot = gr.Chatbot(label="Research Agent", type="messages", height=500)
    textbox = gr.Textbox(label="Your Research Query", placeholder="e.g., 'Latest AI Agent frameworks in 2025'")

    textbox.submit(
        fn=gradio_chat_wrapper,
        inputs=[textbox, chat_state],
        outputs=[chatbot]
    )

ui.launch(inbrowser=True)