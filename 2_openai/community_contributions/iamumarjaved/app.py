import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
import asyncio

load_dotenv(override=True)

# Conversation state
class ConversationState:
    def __init__(self):
        self.stage = "initial"
        self.query = None
        self.email = None
        self.questions = {}
        self.answers = {}
        self.manager = None

state = ConversationState()


def chat(message, history):
    """Main chat function"""
    global state
    
    if not message or not message.strip():
        return history
    
    history = history + [[message, None]]
    
    try:
        if state.stage == "initial":
            state.query = message
            state.manager = ResearchManager("")
            
            history[-1][1] = "Analyzing your query..."
            yield history
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def get_questions():
                async for update in state.manager.get_clarifications(state.query):
                    if update.get("type") == "questions":
                        return update.get("questions")
                return None
            
            questions = loop.run_until_complete(get_questions())
            loop.close()
            
            if questions:
                state.questions = {
                    'email_request': questions.email_request,
                    'question_1': questions.question_1,
                    'question_2': questions.question_2,
                    'question_3': questions.question_3,
                }
                history[-1][1] = f"{questions.email_request}"
                state.stage = "email"
                yield history
            else:
                history[-1][1] = "Sorry, I couldn't generate questions. Please try again."
                state.stage = "initial"
                yield history
        
        elif state.stage == "email":
            if "@" not in message or "." not in message:
                history[-1][1] = "Please provide a valid email address."
                yield history
                return
            
            state.email = message
            state.manager = ResearchManager(state.email)
            history[-1][1] = f"{state.questions['question_1']}"
            state.stage = "q1"
            yield history
        
        elif state.stage == "q1":
            state.answers['answer_1'] = message
            history[-1][1] = f"{state.questions['question_2']}"
            state.stage = "q2"
            yield history
        
        elif state.stage == "q2":
            state.answers['answer_2'] = message
            history[-1][1] = f"{state.questions['question_3']}"
            state.stage = "q3"
            yield history
        
        elif state.stage == "q3":
            state.answers['answer_3'] = message
            history[-1][1] = "Great! Starting research now. This will take a few minutes..."
            yield history
            state.stage = "researching"
            
            answers = {
                'email': state.email,
                'question_1': state.questions['question_1'],
                'answer_1': state.answers['answer_1'],
                'question_2': state.questions['question_2'],
                'answer_2': state.answers['answer_2'],
                'question_3': state.questions['question_3'],
                'answer_3': state.answers['answer_3'],
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def run_research():
                last_status = ""
                report = ""
                async for update in state.manager.run(state.query, answers):
                    if update.get("type") == "status":
                        last_status = update.get("message", "")
                        yield last_status, report, ""
                    elif update.get("type") == "report":
                        report = update.get("message", "")
                        yield last_status, report, ""
                    elif update.get("type") == "email":
                        email_status = update.get("message", "")
                        yield last_status, report, email_status
                
                yield last_status, report, f"Email sent successfully to {state.email}"
            
            gen = run_research()
            while True:
                try:
                    last_status, report, email_status = loop.run_until_complete(gen.__anext__())
                    if report:
                        history[-1][1] = f"**Status:** {last_status}\n\n**Email:** {email_status}\n\n---\n\n{report}"
                    else:
                        history[-1][1] = f"**Progress:** {last_status}"
                    yield history
                except StopAsyncIteration:
                    break
            
            loop.close()
            
            history.append([None, "Research complete! Want to explore another topic? Just type your new query."])
            state = ConversationState()
            yield history
        
        elif state.stage == "done":
            state = ConversationState()
            state.stage = "initial"
            state.query = message
            state.manager = ResearchManager("")
            
            history[-1][1] = "Analyzing your new query..."
            yield history
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def get_questions():
                async for update in state.manager.get_clarifications(state.query):
                    if update.get("type") == "questions":
                        return update.get("questions")
                return None
            
            questions = loop.run_until_complete(get_questions())
            loop.close()
            
            if questions:
                state.questions = {
                    'email_request': questions.email_request,
                    'question_1': questions.question_1,
                    'question_2': questions.question_2,
                    'question_3': questions.question_3,
                }
                history[-1][1] = f"{questions.email_request}"
                state.stage = "email"
                yield history
    
    except Exception as e:
        import traceback
        error_msg = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        history[-1][1] = f"Sorry, an error occurred: {str(e)}"
        yield history


# Enhanced CSS
custom_css = """
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
}

#title-container {
    text-align: center;
    padding: 2rem 1rem 1rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

#title {
    font-size: 2.5rem;
    font-weight: 700;
    color: white;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

#subtitle {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.9);
    margin-top: 0.5rem;
}

.main-content {
    display: flex;
    gap: 1.5rem;
}

.chat-section {
    flex: 1;
    min-width: 0;
}

.sidebar {
    width: 280px;
    flex-shrink: 0;
}

.chatbot-container {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.input-row {
    gap: 8px;
}

.message-bubble-border {
    border-radius: 12px !important;
}

.bot-message {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 18px;
    padding: 12px 16px;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 18px;
    padding: 12px 16px;
    color: white;
}

#info-box {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1.2rem;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    position: sticky;
    top: 20px;
}

#info-box h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.2rem;
}

#info-box p {
    margin: 0.5rem 0;
    line-height: 1.6;
    font-size: 0.95rem;
}

.feature-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    margin: 4px 4px 4px 0;
    font-weight: 500;
}

@media (max-width: 768px) {
    .main-content {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
    }
    
    #info-box {
        position: static;
    }
}
"""

# Create interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="purple", secondary_hue="blue"), css=custom_css) as ui:
    
    with gr.Column(elem_id="title-container"):
        gr.HTML("<h1 id='title'>Deep Research AI</h1>")
        gr.HTML("<p id='subtitle'>Intelligent research assistant with adaptive search evaluation</p>")
    
    with gr.Row(elem_classes=["main-content"]):
        with gr.Column(elem_classes=["chat-section"]):
            chatbot = gr.Chatbot(
                value=[[None, "Hello! I'm your research assistant. What topic would you like me to investigate today?"]],
                height=500,
                show_label=False,
                avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=research"),
                bubble_full_width=False,
                elem_classes=["chatbot-container"]
            )
            
            with gr.Row(elem_classes=["input-row"]):
                msg = gr.Textbox(
                    placeholder="Type your message here...",
                    show_label=False,
                    container=False,
                    scale=9
                )
                submit = gr.Button("Send", variant="primary", scale=1)
            
            clear = gr.Button("Start New Research", variant="secondary", size="sm")
        
        with gr.Column(elem_classes=["sidebar"]):
            with gr.Column(elem_id="info-box"):
                gr.HTML("""
                <h3>How I Work</h3>
                <p>1. Share your research topic</p>
                <p>2. I'll ask clarifying questions</p>
                <p>3. I search, evaluate quality, and re-search if needed</p>
                <p>4. You receive a comprehensive report via email</p>
                <div style="margin-top: 1rem;">
                    <span class="feature-badge">Adaptive Search</span>
                    <span class="feature-badge">Quality Evaluation</span>
                    <span class="feature-badge">Email Delivery</span>
                </div>
                """)
    
    # Event handlers
    def clear_chat():
        global state
        state = ConversationState()
        return [[None, "Hello! I'm your research assistant. What topic would you like me to investigate today?"]], ""
    
    msg.submit(chat, [msg, chatbot], chatbot).then(lambda: "", None, msg)
    submit.click(chat, [msg, chatbot], chatbot).then(lambda: "", None, msg)
    clear.click(clear_chat, None, [chatbot, msg])

if __name__ == "__main__":
    ui.launch(
        server_name="0.0.0.0",
        share=False,
        inbrowser=True
    )
