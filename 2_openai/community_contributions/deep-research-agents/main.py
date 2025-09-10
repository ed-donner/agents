import gradio as gr
from dotenv import load_dotenv
from ai_agents.manager_agent import ManagerAgent
from schema import EmailStatus, ResearchContext, Answer, Question, WebSearchPlan
from utils.loading_message import loading_html


load_dotenv(override=True)

manager = ManagerAgent()

async def agent_chat(user_message: str, chat_history: list[dict[str, str]]):
    temp_history = chat_history + [{"role": "user", "content": user_message}]
    temp_history.append({"role": "assistant", "content": loading_html})
    yield temp_history, chat_history

    if not manager.context.initial_query:
        # First user message is the initial query
        manager.context = ResearchContext(initial_query=user_message, qa_history=[])
    else:
        # For follow-up: attach the user's message as the answer to the last QAItem
        if manager.context.qa_history and manager.context.qa_history[-1].answer is None:
            manager.context.qa_history[-1].answer = Answer(answer=user_message)

    # Run the manager agent with the updated context
    result = await manager.run()

    # Append user message and agent response to chat history
    chat_history.append({"role": "user", "content": user_message})
    if isinstance(result, Question):
        chat_history.append({"role": "assistant", "content": result.question})
    elif isinstance(result, EmailStatus):
        msg = '🔍📝Research Report sent to your email' if result.status == 'success' else result.error_message
        chat_history.append({"role": "assistant", "content": msg})

    yield chat_history, chat_history


def main():
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label="Research Agent", type="messages")
        msg = gr.Textbox(label="Your message")
        state = gr.State([])

        msg.submit(agent_chat, inputs=[msg, state], outputs=[chatbot, state])
        msg.submit(lambda: "", None, msg)

    demo.launch()


if __name__ == "__main__":
    main()
