"""
    Now the system has two tools, one offering general contact
    information on the university, and a second tool that can
    provide information on courses of study at Gravizot University.

    You can change the prompt below to instead ask for details about
    other majors at the university, such as the Graphic Design,
    Electrical Engineering, Bio-informatics, etc. majors.

    Or you can change the prompt to ask for details on a 
    major not offered by the university, such as Political Science,
    and the system should tell you it cannot provide information on that.

    You can change the prompt to instead ask for the University 
    main address, phone number, email address and you should get 
    that information returned. You can also ask for the name of 
    the dean of the university, and you should get a response 
    telling you the agent is unable to provide that.

    You can also change the prompt to ask for information on 
    financial aid offered through the university, or information
    on enrolling in the university and you should get a response 
    telling you the agent is unable to provide that.

    Note that the output might be include markdown, which we do
    not want. The next example will have a more significant 
    prompt to address this issue, but you can play around with
    1_basic_tool_prompt.txt to see if you can achieve:
        - no markdown in output
        - no extra text, just what is in the tool
"""

import os
import asyncio
from dotenv import load_dotenv

dotenv_path = os.getenv("PROJECT_ENV_PATH", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)
from .customer_support_agent import CustomerSupportAgent

async def main():
    agent = CustomerSupportAgent()
    response = await agent.run_task("Give me details about the computer science major at the university.")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
