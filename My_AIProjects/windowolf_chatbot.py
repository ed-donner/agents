from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel


load_dotenv(override=True)

# Create a Pydantic model for the Evaluation
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# Simple lead detection model
class LeadInfo(BaseModel):
    is_lead: bool
    lead_type: str
    name: str
    phone: str
    notes: str

def push(text, title=None, priority=None, sound=None):
    """Send Pushover notification with optional parameters"""
    data = {
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER"),
        "message": text,
    }
    
    if title:
        data["title"] = title
    if priority:
        data["priority"] = priority
    if sound:
        data["sound"] = sound
    
    requests.post("https://api.pushover.net/1/messages.json", data=data)

def push_job_notification(name, phone, notes):
    """Send a job notification when someone leaves contact info"""
    title = "📋 New Job Lead - Windowolf"
    message = f"Name: {name}\nPhone: {phone}\nNotes: {notes}"
    
    push(
        text=message,
        title=title,
        priority=1,  # High priority for job leads
        sound="cashregister"  # Cash register sound for job leads
    )

def push_quality_control_notification(message, reply, feedback):
    """Send a quality control notification when Gemini rejects a response"""
    title = "🔍 Quality Control Alert"
    notification_message = f"User asked: \"{message[:100]}{'...' if len(message) > 100 else ''}\"\n\n"
    notification_message += f"Original reply: \"{reply[:150]}{'...' if len(reply) > 150 else ''}\"\n\n"
    notification_message += f"Judge's feedback: {feedback[:200]}{'...' if len(feedback) > 200 else ''}"
    
    push(
        text=notification_message,
        title=title,
        priority=0,  # Normal priority for quality control
        sound="pushover"  # Default sound for quality control
    )


def record_user_details(phone_number, name="Name not provided", notes="not provided"):
    # Send organized job notification
    push_job_notification(name, phone_number, notes)
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided contact information",
    "parameters": {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "The phone number of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any     itional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["phone_number"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

# Setup Gemini evaluator
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


class Windowolf:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "James Moelling"
        self.business_name = "Windowolf"
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(script_dir, "resources", "windowolf_chatbot.pdf")
        summary_path = os.path.join(script_dir, "resources", "windowolf_summary.txt")
        
        print(f"DEBUG: Script directory: {script_dir}")
        print(f"DEBUG: PDF path: {pdf_path}")
        print(f"DEBUG: Summary path: {summary_path}")
        print(f"DEBUG: PDF exists: {os.path.exists(pdf_path)}")
        print(f"DEBUG: Summary exists: {os.path.exists(summary_path)}")
        
        # Load PDF resources
        try:
            reader = PdfReader(pdf_path)
            self.business_info = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.business_info += text
            print(f"SUCCESS: Loaded PDF with {len(reader.pages)} pages")
            print(f"PDF content length: {len(self.business_info)} characters")
            print(f"PDF preview: {self.business_info[:200]}...")
        except Exception as e:
            print(f"ERROR: Error loading PDF: {e}")
            print(f"ERROR: Looking for PDF at: {pdf_path}")
            self.business_info = "PDF not available"
        
        # Load summary
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                self.summary = f.read()
            print("SUCCESS: Loaded summary successfully")
            print(f"Summary content length: {len(self.summary)} characters")
            print(f"Summary preview: {self.summary[:200]}...")
        except Exception as e:
            print(f"ERROR: Error loading summary: {e}")
            print(f"ERROR: Looking for summary at: {summary_path}")
            self.summary = "Summary not available"


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}, representing both the {self.business_name} window cleaning business and James Moelling personally. You are answering questions on {self.business_name}'s website, \
particularly questions related to window cleaning services, scheduling, the unique pure water cleaning system, and James's background, skills experience, and personal details. \
Your responsibility is to represent both the business and James for interactions on the website as faithfully as possible. \
You are given detailed information about the business, services, cleaning methods, and James's background which you can use to answer questions. \
Be professional and engaging, as if talking to a potential customer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to window cleaning or James's background. \
If the user is engaging in discussion, try to steer them towards getting in touch; ask for their name, phone number, and any notes they'd like to provide, then record it using your record_user_details tool. "

        system_prompt += f"\n\n## Business Summary:\n{self.summary}\n\n## Detailed Business Information:\n{self.business_info}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        
        # Debug: Print system prompt length and preview
        print(f"DEBUG: System prompt length: {len(system_prompt)} characters")
        print(f"DEBUG: System prompt preview: {system_prompt[:300]}...")
        
        return system_prompt
    
    def evaluator_system_prompt(self):
        evaluator_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {self.name} representing the {self.business_name} window cleaning business. \
The Agent has been instructed to be professional and engaging, as if talking to a potential customer who came across the website. \
The Agent has been provided with context on the business and James's background. Here's the information:"
        
        evaluator_prompt += f"\n\n## Business Summary:\n{self.summary}\n\n## Detailed Business Information:\n{self.business_info}\n\n"
        evaluator_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
        return evaluator_prompt
    
    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt
    
    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=Evaluation)
        return response.choices[0].message.parsed
    
    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        return response.choices[0].message.content
    
    def detect_job_lead(self, user_message, bot_response):
        """Simple job lead detection focusing on key info extraction"""
        lead_prompt = f"""Analyze this conversation for a window cleaning business:

User: "{user_message}"
Bot: "{bot_response}"

Extract key information if this is a potential job lead:
- Is this a job lead? (look for: window cleaning requests, pricing questions, scheduling, property details)
- Lead type: "service_request", "pricing", "scheduling", "general", "not_lead"
- Name: Extract any name mentioned
- Phone: Extract any phone number mentioned  
- Notes: Extract any important details (property size, location, urgency, etc.)

Respond with JSON:
{{
    "is_lead": <boolean>,
    "lead_type": "<type>",
    "name": "<name or 'Not provided'>",
    "phone": "<phone or 'Not provided'>", 
    "notes": "<important details or 'None'>"
}}"""
        
        try:
            messages = [{"role": "user", "content": lead_prompt}]
            response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=LeadInfo)
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"Lead detection failed: {e}")
            return LeadInfo(
                is_lead=False,
                lead_type="not_lead",
                name="Not provided",
                phone="Not provided", 
                notes="Detection failed"
            )
    
    
    def chat(self, message, history):
        # Store original user message
        original_message = message
        
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message_obj = response.choices[0].message
                tool_calls = message_obj.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message_obj)
                messages.extend(results)
            else:
                done = True
        
        reply = response.choices[0].message.content
        
        
        # Evaluate the response
        try:
            evaluation = self.evaluate(reply, original_message, history)
            if evaluation.is_acceptable:
                print("SUCCESS: Passed evaluation - returning reply")
                # No notification for successful responses
            else:
                print("FAILED: Failed evaluation - retrying")
                print(f"Feedback: {evaluation.feedback}")
                
                # Send quality control notification
                try:
                    push_quality_control_notification(original_message, reply, evaluation.feedback)
                    print("Quality control notification sent via Pushover")
                except Exception as e:
                    print(f"Failed to send quality control notification: {e}")
                
                reply = self.rerun(reply, original_message, history, evaluation.feedback)
                print("RETRY: Generated new response after feedback")
        except Exception as e:
            print(f"ERROR: Evaluation failed: {e}")
            print("Returning original response")
        
        return reply
    

if __name__ == "__main__":
    windowolf_bot = Windowolf()
    gr.ChatInterface(windowolf_bot.chat, type="messages", title="Windowolf Chatbot").launch()
    