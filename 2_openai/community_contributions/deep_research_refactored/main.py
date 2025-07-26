from agents_manager import AgentManager
from dotenv import load_dotenv
import asyncio


load_dotenv()


if __name__ == "__main__":
    agent_manager = AgentManager(model_name="gpt-4o-mini")
    asyncio.run(agent_manager.run(query="Latest AI Agent frameworks in 2025"))