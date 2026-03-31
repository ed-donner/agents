import os
import requests
import asyncio
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from mcp.client.stdio import stdio_client, ClientSession

load_dotenv()

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Web Search

def web_search(query):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY}
    response = requests.post(url, json={"q": query}, headers=headers)
    data = response.json()

    results = []
    for item in data.get("organic", [])[:3]:
        results.append(item.get("snippet", ""))

    return "\n".join(results)

# LLM Runbook

def generate_runbook(issue):
    context = web_search(issue)

    prompt = f"""
Issue:
{issue}

Context:
{context}

Write a short DevOps runbook with clear steps.
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# MCP Logging

async def log_to_mcp(step):
    params = {
        "command": "python",
        "args": ["server.py"]
    }

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.call_tool("log_runbook_step", {"step": step})

# UI Logic

def chat(issue, history):
    runbook = generate_runbook(issue)

    # log first step (simple example)
    try:
        asyncio.run(log_to_mcp(f"Generated runbook for: {issue}"))
    except:
        pass

    history.append((issue, runbook))
    return history, history

# UI

with gr.Blocks() as app:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Describe your issue")
    btn = gr.Button("Generate Runbook")

    btn.click(chat, [msg, chatbot], [chatbot, chatbot])

app.launch(server_name="0.0.0.0", server_port=7860)