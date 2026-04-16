import os
from dotenv import load_dotenv
import openai
import gradio as gr
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

load_dotenv()

SYSTEM_PROMPT = "You are a deep research assistant. Answer with detailed, well-sourced information."


client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
)

def research_chat(user_message, history):

    # Input guardrail: check for empty or too long input
    if not user_message or not isinstance(user_message, str) or len(user_message.strip()) == 0:
        return "Please enter a valid research question."
    if len(user_message) > 1000:
        return "Your question is too long. Please shorten it to under 1000 characters."

    # Prompt injection filter: block common attack patterns
    injection_patterns = [
        r"ignore (all|any|the)? ?previous instructions?",
        r"disregard (all|any|the)? ?previous instructions?",
        r"pretend (to be|you are)",
        r"you are now",
        r"as an ai language model",
        r"repeat after me",
        r"do anything now",
        r"bypass",
        r"jailbreak",
        r"forget all previous",
        r"act as",
        r"system prompt",
        r"/system",
        r"### system",
        r"assistant:"
    ]
    import re
    for pattern in injection_patterns:
        if re.search(pattern, user_message, re.IGNORECASE):
            return "Your input contains patterns that are not allowed for security reasons. Please rephrase your question."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Gradio history is a list of dicts with 'role' and 'content'
    for turn in history:
        if isinstance(turn, dict) and "role" in turn and "content" in turn:
            messages.append({"role": turn["role"], "content": turn["content"]})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            messages.append({"role": "user", "content": turn[0]})
            messages.append({"role": "assistant", "content": turn[1]})
    messages.append({"role": "user", "content": user_message})

    logging.info("LLM prompt: %s", messages)
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=messages
    )
    result = response.choices[0].message.content.strip()

    # Output guardrail: basic sanitization (remove dangerous HTML, limit length)
    import re
    result = re.sub(r'<(script|iframe|object|embed)[^>]*>.*?</\\1>', '', result, flags=re.IGNORECASE|re.DOTALL)
    if len(result) > 3000:
        result = result[:3000] + "... [output truncated]"

    logging.info("LLM response: %s", result)
    return result

def main():
    print("Welcome to the Deep Research App (OpenRouter, OpenAI SDK compatible)")
    print("Type your research question (or 'quit' to exit):")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        print("AI:", research_chat(user_input, []))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        main()
    else:
        gr.ChatInterface(research_chat, title="Deep Research App (OpenRouter)", description="Ask research questions and get detailed answers.").launch()


       
