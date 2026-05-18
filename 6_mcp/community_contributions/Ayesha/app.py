import os
import asyncio
from dotenv import load_dotenv
import gradio as gr

from agents import Agent, Runner
from agents.mcp import MCPServerStdio


load_dotenv(override=True)


mcp_server_params = [
    {"command": "uv", "args": ["run", "mcp_servers/memory_server.py"]},
    {"command": "uv", "args": ["run", "mcp_servers/nutrition_server.py"]},
    {"command": "uv", "args": ["run", "mcp_servers/coping_server.py"]},
]


async def get_agent():
    servers = [
        MCPServerStdio(params, client_session_timeout_seconds=30)
        for params in mcp_server_params
    ]

    for server in servers:
        await server.connect()

    instructions = """
You are an emotionally intelligent wellbeing assistant.

OUTPUT FORMAT (STRICT):
1. Emotional Acknowledgment
2. Coping Strategies (2-3 bullet points)
3. Food Suggestions (with reason + link)
4. Gentle Closing
5. (Optional) Professional Support Suggestion

RULES:
- Do NOT hallucinate facts
- If unsure, say you’re unsure
- Do NOT give medical diagnosis

FOOD:
- Always include WHY the food helps
- Include a source link

SAFETY:
- If user shows repeated distress, gently suggest professional help

TONE:
- Warm, human, non-judgmental
"""

    agent = Agent(
        name="MoodMCP Agent",
        instructions=instructions,
        model="gpt-4o-mini",
        mcp_servers=servers,
    )

    return agent


async def run_agent(user_input):
    agent = await get_agent()

    result = await Runner.run(
        agent,
        user_input,
        max_turns=10
    )

    return result.final_output


async def chat_async(user_input):
    return await run_agent(user_input)

with gr.Blocks() as app_ui:
    gr.Markdown("Mood MCP")

    user_input = gr.Textbox(
        placeholder="How are you feeling?",
        lines=3
    )

    submit_btn = gr.Button("Submit")

    output = gr.Markdown("Output will appear here...")

    submit_btn.click(
        fn=chat_async,
        inputs=user_input,
        outputs=output
    )

    user_input.submit(
        fn=chat_async,
        inputs=user_input,
        outputs=output
    )

app_ui.launch()