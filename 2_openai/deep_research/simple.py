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
        if len(state["questions"]) == 0:
            state["query"] = message
            state["questions"] = await ResearchManager().run_clarify(message)
            # chat_history.append({"role": "assistant", "content": state["questions"][0].question})
            response = {"role": "assistant", "content": state["questions"][0].question}
            return response, state
        
        elif state["clarify"]:
            for index, question in enumerate(state["questions"]):
                if question.answer is None:
                    question.answer = message
                    # Add next question to chatbot
                    if index + 1 < len(state["questions"]):
                        next_question = state["questions"][index + 1]
                        response = {"role": "assistant", "content": next_question.question}
                        return response, state
                    else:
                        state["clarify"] = False
                        response = []
                        async for status_update in ResearchManager().run(state["query"], state["questions"]):
                            response.append({"role": "assistant", "content": status_update})
                        return response, state  

    chatbot = gr.Chatbot(value=history)
    gr.ChatInterface(respond, chatbot=chatbot, additional_inputs=[state], additional_outputs=[state])


ui.launch(theme=gr.themes.Default(primary_hue="sky"))

