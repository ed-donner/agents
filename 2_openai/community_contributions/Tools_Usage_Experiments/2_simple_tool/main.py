"""
    You can change the prompt below to instead ask for the
    University phone number, email address and you should get
    that information returned. You can also ask for the name
    of the dean of the university, and you should get a 
    response telling you the agent is unable to provide that.
"""

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
