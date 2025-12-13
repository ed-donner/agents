import os
import asyncio
from dotenv import load_dotenv

dotenv_path = os.getenv("PROJECT_ENV_PATH", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

from .customer_support_agent import CustomerSupportAgent

async def main():
    agent = CustomerSupportAgent()
    response = await agent.run_task("What is the address of the University?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
