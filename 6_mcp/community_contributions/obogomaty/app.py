import sys

# MCP SERVER

if "--server" in sys.argv:
    from mcp_server import run as mcp_run
    mcp_run()


# AGENT AND GRADIO UI
else:
    import gradio as gr
    import requests
    from dotenv import load_dotenv
    import os

    load_dotenv(override=True)

    HOME = os.path.expanduser("~")
    SCRIPT = os.path.abspath(__file__)
    MAX_INPUT_LENGTH = 500
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = "gpt-3.5-turbo"  # Widely supported OpenRouter model

    INSTRUCTIONS = f"""You are a helpful file organizer assistant for a Windows PC.

User's home folder: {HOME}
Common folders:
  Downloads: {HOME}\\Downloads
  Documents: {HOME}\\Documents
  Desktop:   {HOME}\\Desktop

You can:
- List files/folders with sizes
- Show which files are largest (to help free up space)
- Find old unused files
- Group files by extension to see what's there
- Create new folders and move files to organize them
- Auto-organize a folder by file type

Rules:
- Always use full absolute paths when calling tools.
- When user says "Downloads", use {HOME}\\Downloads (and similar for other folders).
- Before bulk-moving files, describe the plan and ask for confirmation.
- You do NOT have a delete tool — only listing, creating folders, and moving.
- Be concise and clear in responses.
"""

    def call_openrouter(messages, model=OPENROUTER_MODEL, api_key=OPENROUTER_API_KEY):
        url = "https://openrouter.ai/api/v1/chat/completions"  # Correct endpoint
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.2,
        }
        # Debug output
        print("[DEBUG] OpenRouter API URL:", url)
        print("[DEBUG] Headers (no key):", {k: (v if k != 'Authorization' else 'Bearer ...') for k, v in headers.items()})
        print("[DEBUG] Payload:", payload)
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print("[DEBUG] Status code:", response.status_code)
        print("[DEBUG] Response text:", response.text)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def build_messages(user_message):
        return [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": user_message},
        ]

    def chat(message, history):
        if not message or not message.strip():
            yield "Please type a message."
            return
        if len(message) > MAX_INPUT_LENGTH:
            yield f"Message too long ({len(message)} chars). Max is {MAX_INPUT_LENGTH}."
            return

        try:
            # Call OpenRouter API
            messages = build_messages(message)
            response = call_openrouter(messages)
            yield response
        except Exception as e:
            yield f"Something went wrong: {e}"

    ui = gr.ChatInterface(
        fn=chat,
        title="File System Manager",
        description="I help you organize your files and see what's taking up space.",
        examples=[
            "Display all files in my Downloads folder",
            "Show the biggest files in Downloads",
            "Categorize files by extension in Downloads",
            "Find unused files in Documents older than 6 months",
            "Sort my Downloads folder by file type",
        ],
    )

    if __name__ == "__main__":
        ui.launch(theme="gradio/monochrome")
    
