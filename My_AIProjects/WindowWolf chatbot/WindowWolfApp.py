from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
import google.generativeai as genai
from rag_system.rag_manager import RAGManager




class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Look for .env file in the parent agents directory (two levels up)
env_path = os.path.join(os.path.dirname(os.path.dirname(script_dir)), '.env')
load_dotenv(env_path, override=True)

# Set up Gemini client for evaluation
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')  # Faster model
    GEMINI_AVAILABLE = True
    print("Gemini client configured successfully")
except Exception as e:
    print(f"Gemini not available: {e}")
    gemini_model = None
    GEMINI_AVAILABLE = False

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
    title = "📋 New Job Lead - Window Wolf"
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

def should_evaluate_response(message, reply):
    """Determine if a response should be evaluated based on smart criteria"""
    # Skip evaluation for very short responses (likely simple acknowledgments)
    if len(reply) < 50:
        return False
    
    # Skip evaluation for simple yes/no responses
    simple_responses = ["yes", "no", "ok", "okay", "sure", "absolutely", "definitely", "of course"]
    if reply.lower().strip() in simple_responses:
        return False
    
    # Skip evaluation for responses that are just asking for contact info
    if "phone" in reply.lower() and "number" in reply.lower():
        return False
    
    # Skip evaluation for responses that are just saying "I don't know"
    if "don't know" in reply.lower() or "not sure" in reply.lower():
        return False
    
    # Evaluate longer, more complex responses that might need quality control
    return True


def record_user_details(PhoneNumber, name="Name not provided", notes="not provided"):
    # Send organized job notification
    push_job_notification(name, PhoneNumber, notes)
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an PhoneNumber",
    "parameters": {
        "type": "object",
        "properties": {
            "PhoneNumber": {
                "type": "string",
                "description": "The PhoneNumber of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["PhoneNumber"],
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


class WindowWolf:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "James Moelling"
        self.business_name = "Window Wolf"
        
        # Initialize RAG system
        print("Initializing RAG system...")
        self.rag_manager = RAGManager(base_path=script_dir)
        
        # Load the PDF content (keeping for backward compatibility)
        pdf_path = os.path.join(script_dir, "source_documents", "WindowWolfChatbot.pdf")
        reader = PdfReader(pdf_path)
        self.window_wolf_content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.window_wolf_content += text
        
        # Load the summary (keeping for backward compatibility)
        summary_path = os.path.join(script_dir, "source_documents", "WindowWolfSummary.txt")
        with open(summary_path, "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        # Create evaluator system prompt
        self.evaluator_system_prompt = create_evaluator_system_prompt(
            self.name, self.business_name, self.summary, self.window_wolf_content
        )
        
        print("RAG system initialized successfully!")

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
    
    def system_prompt(self, user_message=None):
        system_prompt = f"""You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s business {self.business_name} and background, skills and experience. \
Your responsibility is to represent {self.name} and {self.business_name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and Skills profile and how {self.business_name} operates and what equipment is used\
which you can use to answer questions. \
Be professional and engaging, as if talking to a potential customer who came across the website. \
If you don't know the answer, say so! \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via text message; ask for their Name, Phone Number and any additional notes they want to provide \
and record it using your record_user_details tool."""

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## WindowWolfChatbot:\n{self.window_wolf_content}\n\n"
        
        # Add RAG-enhanced context if user message is provided
        if user_message:
            rag_context = self.rag_manager.get_context_for_query(user_message)
            if rag_context:
                system_prompt += f"\n\n## Additional Relevant Information (RAG):\n{rag_context}\n\n"
        
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name} who owns and operates {self.business_name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt(user_message=message)}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        
        reply = response.choices[0].message.content
        
        # Smart evaluation: only evaluate responses that might need quality control
        if should_evaluate_response(message, reply):
            print("Evaluating response with Gemini...")
            evaluation = evaluate_with_gemini(reply, message, history, self.evaluator_system_prompt)
            
            if evaluation.is_acceptable:
                print(f"Response accepted")
                return reply
            else:
                print(f"Response rejected")
                print(f"Reason: {evaluation.feedback}")
                
                # Send organized quality control notification
                try:
                    push_quality_control_notification(message, reply, evaluation.feedback)
                    print("Quality control notification sent via Pushover")
                except Exception as e:
                    print(f"Failed to send quality control notification: {e}")
                
                return rerun_with_gemini(reply, message, history, evaluation.feedback, self.system_prompt(user_message=message))
        else:
            print("Skipping evaluation for simple response")
            return reply


def create_evaluator_system_prompt(name, business_name, summary, window_wolf_content):
    """Create the evaluator system prompt for quality assessment"""
    evaluator_system_prompt = f"""You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {name} and is representing {name} and their business {business_name} on their website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential customer who came across the website. \
The Agent has been provided with context on {name} and {business_name} in the form of their summary and business details. Here's the information:"""

    evaluator_system_prompt += f"\n\n## Summary:\n{summary}\n\n## Business Details:\n{window_wolf_content}\n\n"
    evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
    return evaluator_system_prompt


def evaluator_user_prompt(reply, message, history):
    """Create the user prompt for the evaluator"""
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


def evaluate_with_gemini(reply, message, history, evaluator_system_prompt) -> Evaluation:
    """Evaluate a response using Gemini with optimized prompt"""
    if not GEMINI_AVAILABLE:
        # Fallback: simple acceptance if Gemini not available
        return Evaluation(is_acceptable=True, feedback="Gemini not available - response accepted by default")
    
    try:
        # Create a shorter, more focused prompt for faster evaluation
        short_prompt = f"""Evaluate this response from James Moelling (Window Wolf business owner) to a potential customer:

User: "{message}"
Response: "{reply}"

Is this response professional, helpful, and appropriate for a window cleaning business? 

Respond with JSON only:
{{"is_acceptable": true/false, "feedback": "brief feedback"}}"""
        
        response = gemini_model.generate_content(short_prompt)
        response_text = response.text.strip()
        
        # Try to parse JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                eval_data = json.loads(json_str)
                return Evaluation(
                    is_acceptable=eval_data.get("is_acceptable", True),
                    feedback=eval_data.get("feedback", "No feedback provided")
                )
            else:
                # Fallback if no JSON found
                return Evaluation(is_acceptable=True, feedback=f"Could not parse response: {response_text}")
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return Evaluation(is_acceptable=True, feedback=f"JSON parsing failed: {e} - Response: {response_text}")
            
    except Exception as e:
        print(f"Gemini evaluation failed: {e}")
        # Fallback: accept response if evaluation fails
        return Evaluation(is_acceptable=True, feedback=f"Evaluation failed: {e} - response accepted by default")


def rerun_with_gemini(reply, message, history, feedback, system_prompt):
    """Rerun the chat with feedback from the evaluator using Gemini"""
    if not GEMINI_AVAILABLE:
        # Fallback: use OpenAI for rerun if Gemini not available
        openai_client = OpenAI()
        updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content
    
    try:
        updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        
        # Create conversation history for Gemini
        conversation_text = ""
        for entry in history:
            conversation_text += f"User: {entry[0]}\nAssistant: {entry[1]}\n\n"
        conversation_text += f"User: {message}\n"
        
        full_prompt = f"{updated_system_prompt}\n\nConversation:\n{conversation_text}\nPlease provide an improved response:"
        
        response = gemini_model.generate_content(full_prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini rerun failed: {e}")
        # Fallback: return original reply if rerun fails
        return reply



if __name__ == "__main__":
    window_wolf = WindowWolf()
    
    # Create the chat interface
    demo = gr.ChatInterface(
        window_wolf.chat,
        title="Window Wolf - Professional Window Cleaning",
        description="Ask me about window cleaning services, pricing, scheduling, or anything else!",
        examples=[
            "What services do you offer?",
            "How much do you charge for window cleaning?",
            "Do you clean gutters too?",
            "What areas do you serve?",
            "How do I schedule an appointment?"
        ],
        cache_examples=False,
        type="messages"
    )
    
    # Launch the interface
    demo.launch()
    