import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document  # Required for reading the Brain
import gradio as gr

# Load environment variables
load_dotenv(override=True)

# --- Global Configurations ---
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# --- Tool Functions ---

def push(message):
    """Sends a push notification via Pushover."""
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print(f"Pushover not configured. Mock sending: {message}")
        return
    try:
        requests.post(
            PUSHOVER_URL,
            data={"user": PUSHOVER_USER, "token": PUSHOVER_TOKEN, "message": message}
        )
    except requests.RequestException as e:
        print(f"Failed to send push notification: {e}")

def record_user_details(email, name="Not provided", notes="Not provided"):
    """Records user details and sends a notification."""
    push(f"CONTACT: {name} ({email}) - Notes: {notes}")
    return {"status": "Details recorded successfully. I will get back to you."}

def record_unknown_question(question):
    """Records a question the chatbot could not answer."""
    push(f"UNKNOWN QUESTION: '{question}'")
    return {"status": "Question logged for review."}

# --- Tool Definitions (JSON Schema) ---

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Use this tool to record a user's contact details if they want to get in touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "notes": {"type": "string"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Log a question you cannot answer from context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    }
]

# --- Main Application Class ---

class PersonalAI:
    def __init__(self):
        self.openai_client = OpenAI()
        self.name = "Jules Cesar Junior NDAYISENGA"
        self.knowledge_dir = "me/"
        
        # Initialize Knowledge Base
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)
            print(f"Created directory: {self.knowledge_dir}. Please add files.")
            
        self.knowledge_context = self._load_knowledge_base(self.knowledge_dir)
        
        # Debugging check
        print(f"DEBUG: Context Length is: {len(self.knowledge_context)} characters")
        if len(self.knowledge_context) < 100:
            print("WARNING: The AI brain is empty! Check your 'me/' folder.")

        self.system_prompt = self._construct_system_prompt()

    def _scrape_text_from_url(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for item in soup(['script', 'style']):
                item.decompose()
            return ' '.join(line.strip() for line in soup.get_text().splitlines() if line.strip())
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return ''

    def _load_knowledge_base(self, directory):
        full_context = []
        url_list_file = os.path.join(directory, "links.txt")

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            
            # Handle PDF
            if filename.endswith('.pdf'):
                try:
                    reader = PdfReader(path)
                    pdf_text = ''.join(page.extract_text() or '' for page in reader.pages)
                    full_context.append(f'--- Content from {filename} ---\n{pdf_text}')
                    print(f'Loaded PDF: {filename}')
                except Exception as e:
                    print(f'Error reading {filename}: {e}')
            
            # Handle DOCX (The Brain)
            elif filename.endswith('.docx'):
                try:
                    doc = Document(path)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                    full_context.append(f'--- Content from {filename} ---\n{text}')
                    print(f'Loaded DOCX: {filename}')
                except Exception as e:
                    print(f'Error reading DOCX {filename}: {e}')

            # Lightweight markdown / text demos (skip links.txt)
            elif filename.endswith(('.md', '.txt')) and filename != 'links.txt':
                try:
                    with open(path, encoding='utf-8') as fh:
                        text = fh.read()
                    full_context.append(f'--- Content from {filename} ---\n{text}')
                    print(f'Loaded text: {filename}')
                except OSError as e:
                    print(f'Error reading {filename}: {e}')

        # Handle URL Scraping
        if os.path.exists(url_list_file):
            with open(url_list_file, 'r') as f:
                for url in (line.strip() for line in f if line.strip()):
                    print(f'Scraping: {url}')
                    if (scraped_text := self._scrape_text_from_url(url)):
                        full_context.append(f'--- Content from {url} ---\n{scraped_text}')
        
        return '\n\n'.join(full_context)

    def _construct_system_prompt(self):
        return f"""You are a helpful AI assistant acting as {self.name}, representing him on his personal website. 
Your persona is professional, confident, and thoughtful.

Your primary goal is to answer questions about {self.name}'s career, background, and skills using the provided context. 
Speak in the first person ('I').

**Rules & Capabilities:**
1.  **Grounded Answers:** Base your answers strictly on the context provided below. Do not invent information.
2.  **Tool for Unknown Questions:** If you cannot answer a question from the context, you MUST use the `record_unknown_question` tool. Then, inform the user that you don't have the information.
3.  **Tool for Contact:** If the user expresses interest in getting in touch, ask for their email, name, and any relevant notes, then use the `record_user_details` tool to capture this information.
4.  **Persona & Boundaries:** You are an 'Ambivert'—professional but human. You CAN answer personal questions about hobbies (Music, Gaming), favorites (Chocolate, Hugs), and faith if they are in your context. Only refuse questions that are intrusive or unsafe.

--- CONTEXT ---
{self.knowledge_context}
--- END CONTEXT ---"""

    def _handle_tool_calls(self, tool_calls):
        tool_outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Executing tool: {tool_name} with args: {arguments}")

            if tool_name == "record_user_details":
                result = record_user_details(**arguments)
            elif tool_name == "record_unknown_question":
                result = record_unknown_question(**arguments)
            else:
                result = {"error": f"Tool '{tool_name}' not found."}
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result)
            })
        return tool_outputs

    def chat(self, message, history):
        formatted_history = []
        for user_msg, ai_msg in history:
            formatted_history.append({"role": "user", "content": user_msg})
            formatted_history.append({"role": "assistant", "content": ai_msg})
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *formatted_history,
            {"role": "user", "content": message}
        ]

        # Loop to handle recursive tool calls
        while True:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                return response_message.content
            
            # Add tool call to history so the model knows it asked for it
            messages.append(response_message)
            
            tool_outputs = self._handle_tool_calls(tool_calls)
            messages.extend(tool_outputs)

# --- Gradio Interface Launch ---

if __name__ == "__main__":
    ai_instance = PersonalAI()
    
    gradio_interface = gr.ChatInterface(
        ai_instance.chat,
        title="Chat with Samandari (AI Clone) 🇧🇮💻",
        description="""I am a Software Engineer, Founder of Ijwi ry'Ikirundi AI, 
        and a former Nursing student. Ask me about my tech stack, 
        my unique background, or just say hi! (I love chocolate, code, and helping people).""",
        examples=[
            "What is Ijwi ry'Ikirundi AI?", 
            "How does your nursing background help you code?", 
            "What do you do to relax?", 
            "I want to collaborate on a project."
        ],
        theme="soft"
    )
    # Using 0.0.0.0 allows it to be accessed on the local network
    gradio_interface.launch(server_name="0.0.0.0", share=False)