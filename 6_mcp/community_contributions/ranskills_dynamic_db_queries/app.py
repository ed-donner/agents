import os
from pathlib import Path
import asyncio
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent, AgentState

import typer
from rich.console import Console
from rich.markdown import Markdown


from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from agents import Agent

from common import base_dir, logger


load_dotenv(override=True)

logging.getLogger('langchain_mcp_adapters').setLevel(logging.WARNING)

LLM_PROVIDERS = {
    # api_key, base_url, model
    # 'ollama_cloud': (os.getenv('OLLAMA_API_KEY'), 'https://ollama.com/v1', 'gpt-oss:120b'),
    'ollama': (os.getenv('OLLAMA_API_KEY'), 'http://localhost:11434/v1', 'llama3.2:3b'),
    'openai': (os.getenv('OPENAI_API_KEY'), 'https://api.openai.com/v1', 'gpt-4o-mini'),
    'ollama_cloud': (os.getenv('OLLAMA_API_KEY'), 'https://ollama.com/v1', 'gpt-oss:20b'),
    'cerebras': (os.getenv('CEREBRAS_API_KEY'), 'https://api.cerebras.ai/v1', 'llama3.1-8b'),
}
LLM_PROVIDER = 'openai'

api_key, base_url, model = LLM_PROVIDERS[LLM_PROVIDER]


llm = init_chat_model(
    model=model,
    model_provider='openai',
    api_key=api_key,
    base_url=base_url,
)


server_path = base_dir / 'mcp_server/server.py'

client = MultiServerMCPClient(
    {
        'db_server': {
            'transport': 'stdio',
            'command': 'python',
            'args': [str(server_path.absolute())],
        },
    }
)

app = typer.Typer()
console = Console()


@app.command()
def run():
    asyncio.run(main())


async def main():
    global llm
    tools = await client.get_tools()

    console.print(
        Markdown("""
    # 🧠 Chat with your MCP-augmented LLM
    Type '/quit' or '/exit' to exit, or press Ctrl+C / Ctrl+D
    """)
    )

    agent = create_agent(
        model=llm,
        tools=tools,
    )

    while True:
        try:
            user_input = typer.prompt('👤 You')

            if user_input.lower() in {'/quit', '/q', '/exit'}:
                typer.echo('👋 Goodbye!')
                break

            result = await agent.ainvoke({'messages': [{'role': 'user', 'content': user_input}]})
            response = f'✨ **Response**: {result["messages"][-1].content}'
            console.print(Markdown(response))
            print()
        except (EOFError, KeyboardInterrupt):
            typer.echo('👋 Goodbye!')
            break


if __name__ == '__main__':
    app()
