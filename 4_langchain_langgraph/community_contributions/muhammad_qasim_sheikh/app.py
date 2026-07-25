import gradio as gr
import uuid
import asyncio
from langgraph.types import Command
from graph_builder import research_graph

# MAIN CHAT FLOW
async def chat_flow(message: str, state: dict):
    step = state.get("step", "START")
    conversation_id = state.get("conversation_id")

    # START THE GRAPH
    if step == "START":
        conversation_id = str(uuid.uuid4())
        state["conversation_id"] = conversation_id
        state["answers"] = []
        state["step"] = "CLARIFYING"

        yield "Got it! Let’s clarify your intent first."

        config = {"configurable": {"thread_id": conversation_id}}
        initial_input = {"user_query": message}

        try:
            result = await research_graph.ainvoke(initial_input, config=config)

            if "__interrupt__" in result:
                interrupt_payload = result["__interrupt__"][0].value
                raw_questions = interrupt_payload.get("clarifying_questions") if isinstance(interrupt_payload, dict) else interrupt_payload

                normalized_questions = []
                for q in raw_questions or []:
                    if isinstance(q, str):
                        normalized_questions.append(q.strip())
                        continue
                    if isinstance(q, dict):
                        text = q.get("content") or q.get("text") or q.get("question") or q.get("value")
                        if text:
                            normalized_questions.append(str(text).strip())
                            continue
                    text = getattr(q, "content", None) or getattr(q, "text", None) or getattr(q, "question", None)
                    if text:
                        normalized_questions.append(str(text).strip())
                        continue
                    normalized_questions.append(str(q).strip())

                state["questions"] = normalized_questions
                state["question_index"] = 0
                state["step"] = "WAITING_FOR_ANSWERS"

                question_bullets = "\n".join(f"* {q}" for q in normalized_questions)
                
                yield f"Let's clarify a few things. I'll ask you these {len(normalized_questions)} questions one by one:\n\n{question_bullets}"
                await asyncio.sleep(1.0)

                if normalized_questions:
                    yield normalized_questions[0]
                else:
                    yield "No clarifying questions were generated."
            else:
                yield "No clarifications needed, generating report..."
                state["step"] = "PROCESSING"

        except Exception as e:
            yield f"Error during clarification: {e}"
            state["step"] = "START"

    # HANDLE CLARIFYING ANSWERS
    elif step == "WAITING_FOR_ANSWERS":
        state["answers"].append(message)
        idx = state.get("question_index", 0) + 1
        state["question_index"] = idx

        if idx < len(state["questions"]):
            yield state["questions"][idx]
        else:
            yield "Thanks! Generating your research report..."
            state["step"] = "PROCESSING"

            config = {"configurable": {"thread_id": state["conversation_id"]}}

            try:
                result = await research_graph.ainvoke(
                    Command(resume=state["answers"]), config=config
                )

                final_state_snapshot = await research_graph.aget_state(config)
                final_state = final_state_snapshot.values 

                # Get the report
                report = final_state.get('best_report') or final_state.get('report')
                
                # Get the final tool status
                final_tool_status = final_state.get('final_status', 'Processing complete.')

                yield (
                    f"Report Complete!\n\n"
                    f"---\n\n{report[:1000]}...\n\n"
                    f"---\n\n**Actions Taken:**\n{final_tool_status}"
                )

                state["step"] = "START"

            except Exception as e:
                yield f"Error during report generation: {e}"
                state["step"] = "START"

    else:
        yield "Processing already in progress, please wait."


# GRADIO CHAT WRAPPER
async def gradio_chat_wrapper(message: str, session_state: list):
    if not session_state:
        history = []
        state = {"step": "START"}
    else:
        history, state = session_state

    # Add the user message
    history.append((message, None))
    yield history

    async for output in chat_flow(message, state):
        history[-1] = (message, output)
        session_state[:] = [history, state]
        yield history

# GRADIO UI
with gr.Blocks(theme=gr.themes.Soft()) as ui:
    gr.Markdown("# Research Assistant")
    chat_state = gr.State([])
    chatbot = gr.Chatbot(label="AI Research Assistant", height=500)
    textbox = gr.Textbox(label="Enter your topic:", placeholder="e.g. AI in education")

    textbox.submit(gradio_chat_wrapper, [textbox, chat_state], chatbot)

if __name__ == "__main__":
    ui.launch(inbrowser=True)
