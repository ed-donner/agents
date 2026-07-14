import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

history = [
    {"role": "assistant", "content": "What topic would you like to research?"}
]

with gr.Blocks() as ui:
    # Clarify questions
    state = gr.State({
        # Original query of user
        "query": "",
        "questions": [],
        # Need user to answer clarify questions. If all questions are answered, flip to False
        "clarify": True
    })
    
    async def respond(message, chat_history, state):
        chat_history.append({"role": "user", "content": message})
        if len(state["questions"]) == 0:
            state["query"] = message
            state["questions"] = await ResearchManager().run_clarify(message)
            chat_history.append({"role": "assistant", "content": state["questions"][0].question})
            return "", chat_history, state
        
        if state["clarify"]:
            for index, question in enumerate(state["questions"]):
                if question.answer is None:
                    question.answer = message
                    # Add next question to chatbot
                    if index + 1 < len(state["questions"]):
                        next_question = state["questions"][index + 1]
                        chat_history.append({"role": "assistant", "content": next_question.question})
                        return "", chat_history, state
                    else:
                        state["clarify"] = False
                        async for status_update in ResearchManager().run(state["query"], state["questions"]):
                            chat_history.append({"role": "assistant", "content": status_update})
                        return "", chat_history, state
                
        return "", chat_history, state

    chatbot = gr.Chatbot(value=history)
    query_textbox = gr.Textbox(label="Enter your response here...")
    query_textbox.submit(respond, inputs=[query_textbox, chatbot, state], outputs=[query_textbox, chatbot, state])


ui.launch(theme=gr.themes.Default(primary_hue="sky"))

