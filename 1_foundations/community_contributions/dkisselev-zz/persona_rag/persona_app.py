#!/usr/bin/env python3
"""
Persona RAG Application
Gradio interface with RAG integration and Pushover tools
"""
import os
import json
import requests
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from answer import answer_question

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
openai_client = OpenAI()

# Pushover configuration
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

# Model configuration
MODEL = "gpt-4o-mini"

PERSONA_NAME = "Dmitry Kisselev"

def push(message):
    """Send Pushover notification"""
    print(f"Push: {message}")
    if pushover_user and pushover_token:
        try:
            payload = {
                "user": pushover_user,
                "token": pushover_token,
                "message": message
            }
            requests.post(pushover_url, data=payload)
        except Exception as e:
            print(f"Pushover error: {e}")

# Tool functions
def record_user_details(email, name="Name not provided", notes="not provided"):
    """Record user contact details"""
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    """Record questions that couldn't be answered"""
    push(f"Recording question I couldn't answer: {question}")
    return {"recorded": "ok"}

# Tool definitions for OpenAI
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
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
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

def handle_tool_calls(tool_calls):
    """Execute tool calls and return results"""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        
        # Execute the tool
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        
        results.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call.id
        })
    return results

# System prompt
SYSTEM_PROMPT = """You are {PERSONA_NAME}, answering questions about yourself on your personal website.

Speak naturally in first person as if you're talking about your own life, career, and experiences.
Be professional but friendly and conversational.

If someone is engaging in discussion, try to steer them towards getting in touch via email. 
Ask for their email and record it using your record_user_details tool.

If you truly don't know something or cannot answer a question based on the provided context,
use your record_unknown_question tool to record what you couldn't answer.

Relevant context about me:
{context}"""

# System prompt AFTER email is collected
SYSTEM_PROMPT_POST_CONTACT = """You are {PERSONA_NAME}, answering questions about yourself on your personal website.

Speak naturally in first person as if you're talking about your own life, career, and experiences.
Be professional but friendly and conversational.

The user has already shared their contact information with you. Continue the conversation naturally.
If appropriate, you can mention that you're looking forward to connecting via email, but don't ask 
for their email again.

If you truly don't know something or cannot answer a question based on the provided context,
use your record_unknown_question tool to record what you couldn't answer.

Relevant context about me:
{context}"""

def chat(message, history):
    """ Handle chat interaction with RAG and tool support """
    # Get RAG answer and context
    try:
        rag_answer, docs = answer_question(message, history)
        
        # Format context from retrieved documents for tool-enhanced response
        context = "\n\n".join([
            f"[{doc.metadata.get('source', 'unknown')} - {doc.metadata.get('data_type', 'unknown')}]\n{doc.page_content[:300]}..."
            for doc in docs[:5]
        ])
    except Exception as e:
        print(f"RAG error: {e}")
        rag_answer = None
        context = "Unable to retrieve context."
    
    # Check if email has already been collected in this conversation
    email_collected = False
    for h in history:
        if isinstance(h, dict):
            # Check if this message contains a tool call to record_user_details
            if h.get("role") == "assistant" and h.get("tool_calls"):
                for tc in h.get("tool_calls", []):
                    if isinstance(tc, dict) and tc.get("function", {}).get("name") == "record_user_details":
                        email_collected = True
                        break
            if email_collected:
                break
    
    # Choose system prompt based on whether email was collected
    if email_collected:
        system_content = SYSTEM_PROMPT_POST_CONTACT.format(context=context, PERSONA_NAME=PERSONA_NAME)
        print("Using post-contact system prompt", flush=True)
    else:
        system_content = SYSTEM_PROMPT.format(context=context, PERSONA_NAME=PERSONA_NAME)
        print("Using initial system prompt", flush=True)
    
    # If we have a RAG answer, include it as an "assistant draft" in the system prompt
    if rag_answer:
        system_content += f"\n\nDraft answer based on context: {rag_answer}"
    
    messages = [{"role": "system", "content": system_content}]
    
    # Add history (convert Gradio format to OpenAI format if needed)
    for h in history:
        if isinstance(h, dict):
            messages.append(h)
        else:
            # Gradio format: list of [user, assistant] pairs
            messages.append({"role": h["role"], "content": h["content"]})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Tool-calling loop
    done = False
    while not done:
        try:
            response = openai_client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools
            )
            
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "tool_calls":
                # Handle tool calls
                msg = response.choices[0].message
                tool_calls = msg.tool_calls
                results = handle_tool_calls(tool_calls)
                
                # Add to messages
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                })
                messages.extend(results)
            else:
                done = True
        except Exception as e:
            print(f"LLM error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    return response.choices[0].message.content

# Create Gradio interface
demo = gr.ChatInterface(
    chat,
    type="messages",
    title=f"{PERSONA_NAME} - Digital Persona",
    description="Ask me questions about my life, career, skills, and interests!",
    examples=[
        "What is your current position?",
        "Tell me about your experience with machine learning",
        "Where do you live?",
        "What did you do at DataRobot?",
        "What are you working on at The Tensor Lab?"
    ],
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    print("\nStarting Gradio interface...")
    print("\nPushover notifications:", "Enabled" if (pushover_user and pushover_token) else "Disabled")
    
    demo.launch()



