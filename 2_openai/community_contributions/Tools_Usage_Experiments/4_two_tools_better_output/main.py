"""
    The system has the same two tools, one on contact information
    and one on courses of study at Gravizot University.

    But in this newer version of the system, the prompt
    provided to as instructions to the customer support agent 
    instructs the system to never return markdown, only text.
    It also instructs the system to return data using the 
    structure provided by each tool. It also instructs the 
    system to only return data provided by the tool, 
    and to not return any text, such as descriptions, etc.
    that is not provided by the tool.

    Note that the output of this version of the system is
    in JSON format, which is not user friendly. But there 
    should be no markdown, and there should be no additional
    text that does not come from the tools.

    In the next example we will add code that takes this
    structured output and displays it in a user friendly manner.
"""

import os
import asyncio
from dotenv import load_dotenv

dotenv_path = os.getenv("PROJECT_ENV_PATH", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)
from .customer_support_agent import CustomerSupportAgent

async def main():
    agent = CustomerSupportAgent()
    response = await agent.run_task("Give me contact information of the university.")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
