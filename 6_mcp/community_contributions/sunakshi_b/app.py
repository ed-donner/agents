import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(override=True)

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

async def main():
    server_path = Path(__file__).parent / "mcp_server.py"
    # Starting the MCP server passing it through Stdio
    mcp_server_params = [{"command": "uv", "args": ["run", str(server_path)]}]
    mcp_servers = [MCPServerStdio(params, client_session_timeout_seconds=30) for params in mcp_server_params]
    
    for server in mcp_servers:
        await server.connect()

    instructions = """
You are an empathetic Exam Preparation Coach. You have access to tools that store and retrieve study materials and flashcards from an MCP server database.
Every session, adapt your coaching tone based on the user's mood and interest.
1. When the user tells you their mood and interest and chosen topic, search for the topic using the available tools.
2. If the user doesn't specify a topic, list the currently available topics and ask what they'd like to dive into today.
3. If flashcards don't exist for the topic, create Q&A pairs from the retrieved study material, save them to the database using the tools, and present them.
4. For training better memorization, start asking the user the flashcard questions ONE AT A TIME. Wait for their answer, provide feedback, and continue to the next.
5. If the user wants to add new study material to a topic, process it and save it using your tools.
Keep your responses encouraging!
"""

    agent = Agent(
        name="Exam Coach",
        instructions=instructions,
        mcp_servers=mcp_servers,
        model="gpt-4o-mini"
    )

    print("ExamPrep Coach: Hello! How are you feeling today? What is your interest level, and what topic would you like to study?")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("ExamPrep Coach: Keep up the great work! Catch you later.")
                break
            
            with trace("Exam Coach"):
                result = await Runner.run(agent, user_input, max_turns=15)
            print(f"\nExamPrep Coach:\n{result.final_output}")
            
        except KeyboardInterrupt:
            print("\nExamPrep Coach: Keep up the great work! Catch you later.")
            break

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable.")
        sys.exit(1)
    asyncio.run(main())
