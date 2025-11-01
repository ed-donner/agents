from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from agents import Agent, Runner, trace, function_tool, OpenAIChatCompletionsModel
import os
import gradio as gr
import requests
import asyncio

# Load environment variables
load_dotenv(override=True)
openai_client = OpenAI()

# Setup Google Gemini client
google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=gemini_client)

# Load company profile
name = "CBTW"
with open(f"profiles/{name}.txt", "r", encoding="utf-8") as f:
    summary = f.read()

# Pushover notification setup
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    """Send push notification via Pushover"""
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

# Agent instruction
instruction = f"""You are {name}, the virtual representative of {name}. Your role is to assist visitors on the {name} website by answering questions about the company's information, services, and career opportunities. 
Respond professionally and engagingly, as if speaking to a potential client or future employee. Use the provided company summary to ensure accurate and authentic answers.
If you don't know the answer, politely acknowledge it instead of guessing.
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated. \
If the user is engaging in carrer, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. """

instruction += f"\n\nSummary:\n<Summary>{summary}</Summary>\n\n"
instruction += f"With this context, please chat with the user, always staying in character as {name}."

# Define tools
@function_tool
def record_user_details(email, name="Name not provided", notes="not provided"):
    """
    Record user contact information and interest details for follow-up.
    
    Use this when a user expresses interest in your carrer/product/service or wants to be contacted.
    Call this function when the user provides their email address or asks to be contacted.
    
    Args:
        email: User's email address (required)
        name: User's full name (optional, defaults to "Name not provided")
        notes: Additional context about their interest, questions, or requirements (optional)
    
    Returns:
        dict: Confirmation that the details were recorded
    """
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

@function_tool
def record_unknown_question(question):
    """
    Log questions that the agent cannot answer for future improvement.
    
    Use this when a user asks something you don't have information about or can't answer.
    This helps track knowledge gaps and improve the agent's capabilities over time.
    
    Args:
        question: The exact question or topic the user asked about that you couldn't answer
    
    Returns:
        dict: Confirmation that the question was recorded
    """
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}

tools = [record_user_details, record_unknown_question]

# Create agent
cbtw_chat_agent = Agent(
    name="CBTW Chat Agent",
    instructions=instruction,
    model=gemini_model,
    tools=tools
)

# Store conversation history
conversation_history = []
conversation_max_message = 20

async def cbtw_chat(message, history):
    """Handle chat interactions"""
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    max_iterations = 5  # Prevent infinite loops
    iteration = 0
    
    with trace("CBTW Chat Agent"):
        while iteration < max_iterations:
            result = await Runner.run(cbtw_chat_agent, conversation_history)
            iteration += 1
            print(result)
            # Check if the result contains a tool call
            has_tool_call = False
            if hasattr(result, 'messages') and result.messages:
                last_message = result.messages[-1]
                if last_message.get('tool_calls'):
                    has_tool_call = True
                    # Add the tool call message and result to history
                    conversation_history.append(last_message)
            
            # If there's a final text response, break
            if hasattr(result, 'final_output') and result.final_output:
                response = result.final_output
                break
            
            # If no tool call and no final output, we're stuck
            if not has_tool_call:
                response = """Thank you for your question! I’m sorry, but I don’t have the exact answer for that right now. I’ve forwarded your message to our admin team \
                    so they can assist you further.
                    Please feel free to continue sharing any other questions or details. We’re here to help! 😊"""
                break
        
        # Add assistant response to history
        if response:
            conversation_history.append({
                "role": "assistant",
                "content": response
            })
        
        # Keep only the last N messages
        if len(conversation_history) > conversation_max_message:
            conversation_history[:] = conversation_history[-conversation_max_message:]
        
        return response

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "CBTW"
        with open(f"profiles/CBTW.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self.conversation_history = []
        self.conversation_max_message = 20
    
    
    async def chat(self, message, history):
        conversation_history.append({
            "role": "user",
            "content": message
        })
        
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        with trace("CBTW Chat Agent"):
            while iteration < max_iterations:
                result = await Runner.run(cbtw_chat_agent, conversation_history)
                iteration += 1
                print(result)
                # Check if the result contains a tool call
                has_tool_call = False
                if hasattr(result, 'messages') and result.messages:
                    last_message = result.messages[-1]
                    if last_message.get('tool_calls'):
                        has_tool_call = True
                        # Add the tool call message and result to history
                        conversation_history.append(last_message)
                
                # If there's a final text response, break
                if hasattr(result, 'final_output') and result.final_output:
                    response = result.final_output
                    break
                
                # If no tool call and no final output, we're stuck
                if not has_tool_call:
                    response = """Thank you for your question! I’m sorry, but I don’t have the exact answer for that right now. I’ve forwarded your message to our admin team \
                        so they can assist you further.
                        Please feel free to continue sharing any other questions or details. We’re here to help! 😊"""
                    break
            
            # Add assistant response to history
            if response:
                conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            # Keep only the last N messages
            if len(conversation_history) > conversation_max_message:
                conversation_history[:] = conversation_history[-conversation_max_message:]
            
            return response
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    