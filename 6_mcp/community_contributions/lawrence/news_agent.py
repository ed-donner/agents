import os
import asyncio
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack

import gradio as gr
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import Agent, Runner, trace, ModelSettings
from agents.mcp import MCPServerStdio

# =========================
# ENV SETUP
# =========================
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY missing")

# Fix Windows asyncio issue
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =========================
# MCP SERVERS
# =========================
search_server_params = {"command": "uv", "args": ["run", "news_search_server.py"]}
push_server_params = {"command": "uv", "args": ["run", "news_push_server.py"]}

model = "gpt-4.1-mini"

# =========================
# STRUCTURED OUTPUT
# =========================
class ReviewOutput(BaseModel):
    approved: bool = Field(description="Whether result is important")
    reason: str = Field(description="Explanation")

# =========================
# AGENTS
# =========================
def search_agent(servers):
    return Agent(
        name="Search Agent",
        instructions="""
Search for current information using tools.
Return a clear and concise summary.
""",
        mcp_servers=servers,
        model=model,
        model_settings=ModelSettings(temperature=0.3),
    )

def reviewer_agent():
    return Agent(
        name="Reviewer Agent",
        instructions="""
Decide if the information is important enough to notify the user.

Approve if:
- recent
- meaningful or impactful

Reject if:
- trivial
- irrelevant
""",
        output_type=ReviewOutput,
        model=model,
    )

def notifier_agent(servers):
    return Agent(
        name="Notifier Agent",
        instructions="""
Send a push notification with a short summary.
""",
        mcp_servers=servers,
        model=model,
    )

# =========================
# GUARDRAILS
# =========================
def validate_input(query: str):
    q = query.strip()

    if not q:
        raise ValueError("Query cannot be empty")

    if len(q) < 5:
        raise ValueError("Please provide more detail")

    if len(q) > 300:
        raise ValueError("Query too long")

    banned = ["hack", "illegal", "exploit"]
    for word in banned:
        if word in q.lower():
            raise ValueError("Unsafe query detected")

# =========================
# AGENT PIPELINE
# =========================
async def run_agent(user_message: str) -> AsyncIterator[str]:
    try:
        validate_input(user_message)
    except ValueError as e:
        yield str(e)
        return

    async with AsyncExitStack() as stack:
        servers = [
            await stack.enter_async_context(
                MCPServerStdio(s, client_session_timeout_seconds=120)
            )
            for s in [
                search_server_params,
                push_server_params
            ]
        ]

        with trace("News Agent"):
            yield "Searching...\n"

            search = search_agent(servers)
            search_result = await Runner.run(search, user_message)

            yield "Reviewing results...\n"

            reviewer = reviewer_agent()
            review = await Runner.run(reviewer, search_result.final_output)

            if not review.final_output.approved:
                yield f"Not important:\n{review.final_output.reason}"
                return

            yield "Sending notification...\n"

            notifier = notifier_agent(servers)
            await Runner.run(
                notifier,
                f"Send this:\n{search_result.final_output[:300]}"
            )

            yield "Notification sent.\n\n"
            yield search_result.final_output

# =========================
# GRADIO STREAMING UI
# =========================
async def chat_fn(message, history):
    history = history or []
    history.append([message, ""])
    yield history

    async for chunk in run_agent(message):
        history[-1][1] += chunk
        yield history

# =========================
# UI
# =========================
with gr.Blocks(title="News Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# News Intelligence Agent")

    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(placeholder="Ask for latest news...")

    msg.submit(chat_fn, [msg, chatbot], chatbot)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    demo.launch()