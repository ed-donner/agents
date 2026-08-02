from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from agents import Agent, Runner
import asyncio

import os



async def test_agent_run():
    async def test_agent(message):
        test_agent = Agent(name="test agent", instructions="Your job is to say only a single word (not more than one) reflecting the meaning of the user's prompt")
        result = await Runner.run(test_agent, message)
        return result

    loop = asyncio.get_running_loop()
    result = await loop.test_agent(test_agent("hi!"))
    print('SUCCESSFULLY LOADED MODEL'+result)


async def load_models(baseUrl: str, api_key: str):
     
    claude_client = AsyncOpenAI(base_url=baseUrl, api_key=claude_api_key)
    claude_model = OpenAIChatCompletionsModel(model="haiku", openai_client=claude_client)
    
    test_agent_run()

    return claude_model
    

claude_api_key = os.getenv('CLAUDE_API_KEY')  
CLAUDE_MODEL=await load_models("https://api.anthropic.com/v1", claude_api_key)

__all__ = ['CLAUDE_MODEL'] 