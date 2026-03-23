from linkedin_manager_agent import linkedin_manager_agent
from agents import Runner, trace
import asyncio


async def run_linkedin_update():
    """Run the LinkedIn manager agent to create and publish a LinkedIn post"""
    message = "Create and publish my latest coding update."
    with trace("LinkedIn Manager Agent"):
        result = await Runner.run(linkedin_manager_agent, message)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(run_linkedin_update())

