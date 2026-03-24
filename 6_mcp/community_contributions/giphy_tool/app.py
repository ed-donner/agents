import re
import asyncio
import gradio as gr
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
import os
from pydantic import BaseModel

load_dotenv(override=True)

class GiphyToolResult(BaseModel):
    url: str
    text: str

# You need a GIPHY_API_KEY in your .env file to run this app.
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
params = {
    "command": "npx",
    "args": ["-y", "mcp-server-giphy"],
    "env": {"GIPHY_API_KEY": GIPHY_API_KEY or ""},
}

INSTRUCTIONS = (
    "You use the Giphy tool to find GIFs. "
    "Reply with a short message and include the chosen GIF as a image URL"
)


async def search(query: str):
    q = (query or "").strip()
    if not q:
        return None, "Enter a query."
    model = "gpt-4.1-mini"
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(
            name="giphy_tool",
            instructions=INSTRUCTIONS,
            model=model,
            mcp_servers=[mcp_server],
            output_type=GiphyToolResult,
        )
        with trace("Meme Generator"):
            result = await Runner.run(agent, q)
        print(f"Result: {result.final_output}")
        return result.final_output.url, result.final_output.text

with gr.Blocks() as demo:
    gr.Markdown("## Meme Generator using Giphy tool")
    query = gr.Textbox(label="Query", value="A happy dancing cat")
    go = gr.Button("Generate Meme")
    img = gr.Image(label="Result") 
    reply = gr.Markdown()
    go.click(search, [query], [img, reply])

if __name__ == "__main__":
    demo.queue()
    demo.launch()