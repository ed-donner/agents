import os
import json
import requests
from bs4 import BeautifulSoup
import gradio as gr
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv(override=True)

# Configuration
MODEL_ID = "moonshotai/Kimi-K2.5"
client = InferenceClient(MODEL_ID, token=os.getenv("HUGGINGFACE_TOKEN"))

# Push notification function

def push_notification(message):
    """Sends a high-priority alert to your phone via Pushover."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": message,
        }
    )

def record_user_details(email, name="Not provided", notes="No notes"):
    push_notification(f"LEAD ALERT: {name} ({email}) is interested. Context: {notes}")
    return {"status": "success", "message": "Details recorded for follow-up."}

def record_unknown_question(question):
    push_notification(f"KNOWLEDGE GAP: I couldn't answer: {question}")
    return {"status": "logged", "message": "Question recorded for the human version of me to review."}

# Perform web scrapping to get the latest content

def browse_live_content(source):
    urls = {
        "medium": "https://medium.com/@freemangoja",
        "speaker": "https://world.aiacceleratorinstitute.com/location/agenticaitoronto/speaker/freemangoja",
        "ailysis": "https://ailysis.io"
    }
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(urls.get(source), headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup(["script", "style"]): s.decompose()
        return " ".join(soup.stripped_strings)[:2000]
    except Exception as e:
        return f"Browsing error: {str(e)}"

def query_github():
    try:
        res = requests.get("https://api.github.com/users/frex1/repos")
        return [{"name": r["name"], "desc": r["description"]} for r in res.json() if not r.get("private")]
    except:
        return "GitHub unavailable."

# Tool Schema
tools = [
    {"type": "function", "function": {"name": "query_github", "description": "View public projects on GitHub (frex1)."}},
    {"type": "function", "function": {
        "name": "browse_live_content",
        "description": "Scrape personal technical content.",
        "parameters": {
            "type": "object",
            "properties": {"source": {"type": "string", "enum": ["medium", "speaker", "ailysis"]}},
            "required": ["source"]
        }
    }},
    {"type": "function", "function": {
        "name": "record_user_details",
        "description": "Record contact info for recruiters or collaborators.",
        "parameters": {
            "type": "object",
            "properties": {"email": {"type": "string"}, "name": {"type": "string"}, "notes": {"type": "string"}},
            "required": ["email"]
        }
    }},
    {"type": "function", "function": {
        "name": "record_unknown_question",
        "description": "Log questions that the AI cannot answer accurately.",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"]
        }
    }}
]

# Create a digital twin class

class DigitalTwin:
    def __init__(self):
        self.system_prompt = (
            "You are the AI Digital Twin of a Senior AI Engineer & Data Scientist(12+ yrs), and MIT Mentor. "
            "You founded AIlysis and SnapSlip."
            "You write articles on Medium and speak at AI conferences including AIAI Toronto. "
            "Tone: Friendly, insightful, professional, entrepreneurial. "
            "Always use tools to verify facts before answering deep technical or personal questions."
            "Keep your responses concise and to the point."
            "If you don't know the answer to a question, say so and use the record_unknown_question tool to record the question."
            "After a discussion, try to steer the user towards getting in touch via email; ask for their email and name and record it using your record_user_details tool."
            "If the user is asking about your projects, use the query_github tool to access your GitHub repositories."
            "If the user is asking about your experience, use the query_github tool to access your GitHub repositories."
            "If the user is asking about your skills, use the browse_live_content tool to access your latest content."
        )

    def chat_stream(self, history):
        if history is None: history = []
        messages = [{"role": "system", "content": self.system_prompt}] + history

        # STEP 1: Tool Decision Phase
        response = client.chat_completion(messages=messages, tools=tools, tool_choice="auto", max_tokens=1000)
        assistant_msg = response.choices[0].message
        
        if assistant_msg.tool_calls:
            for tool_call in assistant_msg.tool_calls:
                t_name = tool_call.function.name
                t_args = tool_call.function.arguments
                
                if isinstance(t_args, str):
                    try:
                        t_args = json.loads(t_args)
                    except json.JSONDecodeError:
                        t_args = {} 

                reasoning = {
                    "query_github": "Searching my GitHub (frex1) for technical implementation details...",
                    "browse_live_content": f"Accessing my latest {t_args.get('source', 'content')} updates...",
                    "record_user_details": "Securely recording your contact details...",
                    "record_unknown_question": "Flagging this question for a human response..."
                }.get(t_name, "Analyzing context...")
                
                history.append(gr.ChatMessage(role="assistant", content=reasoning, metadata={"title": "Reasoning"}))
                yield history

                if t_name == "query_github": 
                    result = query_github()
                elif t_name == "browse_live_content": 
                    result = browse_live_content(t_args.get("source"))
                elif t_name == "record_user_details": 
                    result = record_user_details(**t_args)
                elif t_name == "record_unknown_question": 
                    result = record_unknown_question(t_args.get("question"))
                
                messages.append(assistant_msg)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": t_name, "content": json.dumps(result)})

        # Answer with Streaming
        history.append(gr.ChatMessage(role="assistant", content=""))
        stream = client.chat_completion(messages=messages, max_tokens=1000, stream=True)
        
        full_response = ""
        for chunk in stream:
            if not chunk.choices:
                continue
                
            token = chunk.choices[0].delta.content
            if token:
                full_response += token
                history[-1].content = full_response
                yield history

# UI 

with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {background-color: #0b1120;}") as demo:
    gr.HTML("<h1 style='color: white; text-align: center;'>AI Digital Twin: Senior AI Engineer, Data Scientist & Mentor</h1>")
    chatbot = gr.Chatbot(type="messages", label="Professional AI Persona", height=600)
    msg_input = gr.Textbox(placeholder="Ask me about AI, Machine Learning or Mentorship...", show_label=False)
    
    twin = DigitalTwin()

    def user_msg(user_message, history):
        if history is None: history = []
        return "", history + [gr.ChatMessage(role="user", content=user_message)]

    msg_input.submit(user_msg, [msg_input, chatbot], [msg_input, chatbot], queue=False).then(
        twin.chat_stream, [chatbot], [chatbot]
    )

if __name__ == "__main__":
    demo.launch()