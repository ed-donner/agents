from agents import Agent
from craft_post_agent import craft_post_agent
from tools import post_to_linkedin  # your LinkedIn posting tool
from agents import Runner, trace
import asyncio
from dotenv import load_dotenv
load_dotenv(override=True)

# wrap the craft_post_agent so it can be called as a tool
craft_post_tool = craft_post_agent.as_tool(
    tool_name="craft_post_agent",
    tool_description="Generate a LinkedIn post based on the user's recent files code changes"
)

linkedin_manager_instructions = """
You are a LinkedIn manager.
Workflow:
1. Call the craft_post_agent tool to generate the LinkedIn post.
2. Post that exact content using the post_to_linkedin tool. Do not post using the post_to_linkedin tool if craft_post_agent returns an empty or no content.
3. Do not ask the user or modify the post.
"""

linkedin_manager_agent = Agent(
    name="LinkedInManagerAgent",
    instructions=linkedin_manager_instructions,
    tools=[post_to_linkedin, craft_post_tool],
    model="gpt-4o-mini",
)

async def main():
    message = "create a post for LinkedIn"
    with trace("LinkedIn Manager Agent"):
        result = await Runner.run(linkedin_manager_agent, message)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())