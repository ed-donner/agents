# agents/craft_post_agent.py
from agents import Agent
from tools import get_recent_files_context
from agents import Runner, trace

from dotenv import load_dotenv
import asyncio

craft_post_agent_instructions = """
You create LinkedIn posts for software engineers.

First, call the tool to read the files modified in the last 24 hours.
Then write a concise LinkedIn post (maximum 150 words) describing what was worked on.

Focus on:
- What os the project about
- Core skills covered
- What was learned
- Next steps in improving the project

You can uses some relevant emojis to make it lively and engaging

Return only the post text.
No headings, no formatting, no explanations.

Posts should be written in first person, as if you are the one who did the work.
"""	

craft_post_agent = Agent(
    name="CraftPostAgent",
    instructions=craft_post_agent_instructions,
    tools=[get_recent_files_context],
    model="gpt-4o-mini",
)

async def main():
    message = "create a post for LinkedIn"
    with trace("Craft Post Agent"):
        result = await Runner.run(craft_post_agent, message)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())