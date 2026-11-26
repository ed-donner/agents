from agents import Runner
from managers import sales_manager


async def run_agent(prompt: str):

    result = await Runner.run(sales_manager, prompt)
    return result
