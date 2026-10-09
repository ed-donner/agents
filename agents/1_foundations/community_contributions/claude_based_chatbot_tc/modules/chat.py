"""
Chat functionality for the Claude-based chatbot
"""
import re
import time
import json
from collections import deque
from anthropic import Anthropic
from .config import MODEL_NAME, MAX_TOKENS
from .tools import tool_schemas, handle_tool_calls
from .data_loader import load_personal_data

# Initialize Anthropic client
anthropic_client = Anthropic()

def sanitize_input(text):
    """Protect against prompt injection by sanitizing user input"""
    return re.sub(r"[^\w\s.,!?@&:;/-]", "", text)

def create_system_prompt(name, summary, linkedin):
    """Create the system prompt for Claude"""
    return f"""You are acting as {name}. You are answering questions on {name}'s website, 
particularly questions related to {name}'s career, background, skills and experience.
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. 
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions.
Be professional and engaging, as if talking to a potential client or future employer who came across the website, and only mention company names if the user asks about them.

IMPORTANT: When greeting users for the first time, always start with: "Hello! *Meet {name}'s AI assistant, trained on her career data.* " followed by your introduction.

Strict guidelines you must follow:
- When asked about location, do NOT mention any specific cities or regions, even if asked repeatedly. Avoid mentioning cities even when you are referring to previous work experience, only use countries.
- Never share {name}'s email or contact information directly. If someone wants to get in touch, ask for their email address (so you can follow up), or encourage them to reach out via LinkedIn.
- If you don't know the answer to any question, use your record_unknown_question tool to log it.
- If someone expresses interest in working together or wants to stay in touch, use your record_user_details tool to capture their email address.
- If the user asks a question that might be answered in the FAQ, use your search_faq tool to search the FAQ.
- If you don't know the answer, say so.

## Summary:
{summary}

## LinkedIn Profile:
{linkedin}

With this context, please chat with the user, always staying in character as {name}.
"""

def chat_function(message, history, state=None):
    """
    Main chat function that:
    1. Applies rate limiting
    2. Sanitizes input
    3. Handles Claude API calls
    4. Processes tool calls
    5. Adds disclaimer to responses
    """
    # Load data
    data = load_personal_data()
    name = "Taissa Conde"
    summary = data["summary"]
    linkedin = data["linkedin"]
    
    # Disclaimer to be shown with the first response
    disclaimer = f"""*Note: This AI assistant, trained on her career data and is a representation of professional information only, not personal views, and details may not be fully accurate or current.*"""
    
    # Rate limiting: 10 messages/minute
    if state is None:
        state = {"timestamps": deque(), "full_history": [], "first_message": True}

    # Check if this is actually the first message by looking at history length
    is_first_message = len(history) == 0
    
    now = time.time()
    state["timestamps"].append(now)
    while state["timestamps"] and now - state["timestamps"][0] > 60:
        state["timestamps"].popleft()
    if len(state["timestamps"]) > 10:
        return "⚠️ You're sending messages too quickly. Please wait a moment."

    # Store full history with metadata for your own use
    state["full_history"] = history.copy()

    # Sanitize user input
    sanitized_input = sanitize_input(message)
    
    # Format conversation history for Claude - NO system message in messages array
    # Clean the history to only include role and content (remove any extra fields)
    messages = []
    for turn in history:
        # Only keep role and content, filter out any extra fields like metadata
        clean_turn = {
            "role": turn["role"],
            "content": turn["content"]
        }
        messages.append(clean_turn)
    messages.append({"role": "user", "content": sanitized_input})
    
    # Create system prompt
    system_prompt = create_system_prompt(name, summary, linkedin)
    
    # Process conversation with Claude, handling tool calls
    done = False
    while not done:
        response = anthropic_client.messages.create(
            model=MODEL_NAME,
            system=system_prompt,  # Pass system prompt as separate parameter
            messages=messages,
            max_tokens=MAX_TOKENS,
            tools=tool_schemas,
        )
        
        # Check if Claude wants to call a tool
        # In Anthropic API, tool calls are in the content blocks, not a separate attribute
        tool_calls = []
        assistant_content = ""
        
        for content_block in response.content:
            if content_block.type == "text":
                assistant_content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append(content_block)
        
        if tool_calls:
            results = handle_tool_calls(tool_calls)
            
            # Add Claude's response with tool calls to conversation
            messages.append({
                "role": "assistant", 
                "content": response.content  # Keep the original content structure
            })
            
            # Add tool results
            messages.extend(results)
        else:
            done = True
    
    # Get the final response and add disclaimer
    reply = ""
    for content_block in response.content:
        if content_block.type == "text":
            reply += content_block.text
    
    # Remove any disclaimer that Claude might have added
    if reply.startswith("📌"):
        reply = reply.split("\n\n", 1)[-1] if "\n\n" in reply else reply
    if "*Note:" in reply:
        reply = reply.split("*Note:")[0].strip()

    # Add disclaimer only to first message and at the bottom
    if is_first_message:
        return f"{reply.strip()}\n\n{disclaimer}", state
    else:
        return reply.strip(), state